"""
pull_instagram.py — Phase 3.

Costs Apify credit, so this is incremental by construction: each call to the
actor is bounded to "posts newer than" the earlier of (a) the brand's newest
stored post and (b) the 10-day refresh window, which in one request both
picks up genuinely new posts AND re-buys view/engagement counts for posts
still young enough for their view curve to be moving. That 10-day bound is
also what keeps monthly volume near ~300 posts instead of ~900, which is
what keeps this inside the $5/mo free credit.

Refuses to run for real (non-dry-run) while ANY brand in config.py has
`verified: False` — a wrong handle silently produces wrong data for that
brand, and this is the one ingestion source where a scrape can quietly point
at the wrong account. `--dry-run` makes no network call and no store write,
so it is exempt from the gate — it exists specifically to sanity-check
what a real run would fetch *before* verification and spend.

`handle_ig` is always a LIST, even for a brand with one handle — most
brands run one account, but a brand can legitimately run more than one
(McDonald's India is split between two franchise operators, Westlife and
CPRL, each with its own Instagram account; one brand to a consumer, two
accounts to this pipeline). Every handle is pulled and stored under the
same brand_id; `mark_cross_handle_duplicates()` then flags posts that are
the same corporate creative cross-posted to more than one of a brand's own
handles (matched on caption + timestamp proximity, since the two accounts
publish separate copies of the same creative, not a share/repost with a
shared post ID) so that content gets counted once, not once per handle,
in every post-count-based stat — its real, separately-earned engagement
still counts in full toward visibility, since two different audiences
really did see and react to it.

Two under-fetch failure modes this file guards against, both silent by
default because the actor call itself still returns HTTP 200:

  1. Apify's actor runs logged-out (it cannot use a login/session for any
     profile — that's a hard Apify platform restriction, not a config
     option) and Instagram serves a reduced or fully gated view to
     logged-out viewers on accounts with the alcohol/sensitive-content age
     gate turned on. When that happens the actor doesn't return posts at
     all — it returns a single item carrying an `error`/`errorDescription`
     (or `isRestrictedProfile`) field instead of post data. Left unfiltered,
     `build_post_record()` would mostly discard that item for lacking an
     `id`, and the run would just look like "this brand posted once" —
     indistinguishable from a real quiet quarter. `_is_restricted_item()`
     detects and logs this explicitly instead.
  2. Even without an explicit error item, an account can simply come back
     thin for a request that should have paginated further. `run()` logs
     the raw (pre-filter) item count for every brand/handle/request, and if
     a brand we have a follower count for (>10k) comes back with fewer
     than 3 non-duplicate posts in the trailing 90 days, that's flagged as
     a `warn` with the raw response attached to pull_log — never passed
     through as a normal "low-volume brand" without a trace.

A partial pull commits what it got. `run()` tracks per-brand success
independently of the whole-run status: a brand's exception (including
`ApifyQuotaExceeded` on a 403 — Apify's free credit exhausted mid-run) is
recorded and the loop moves on to the next brand rather than aborting.
`store.save_posts()` runs once, after the loop, unconditionally — so 6
brands' worth of real rows are never thrown away because a 7th brand's
credit ran out. The whole run only fails (`status="error"`, non-zero
exit) when NOT ONE attempted brand succeeded; any partial success is
`"warn"` and still exits 0, because a downstream CI step that stops the
job on a non-zero exit must not also discard everything a partially
successful run already fetched. A confirmed quota exhaustion also skips
every *remaining* brand for this run (they'd all 403 identically) instead
of rediscovering that fact brand by brand.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

from . import config, store, usage

APIFY_API = "https://api.apify.com/v2"
DEFAULT_ACTOR = "apify~instagram-scraper"
RESULTS_LIMIT = 200

# Volume guard (see module docstring, failure mode 2): a brand this big
# posting fewer than this many times in 90 days is far more likely an
# under-fetch than a genuine near-silent account.
VOLUME_GUARD_FOLLOWER_FLOOR = 10_000
VOLUME_GUARD_MIN_POSTS_90D = 3

# Cross-handle dedup (module docstring): two franchise accounts posting the
# same corporate creative almost always do so the same day. Wide enough to
# catch a same-day-different-timezone-of-upload gap, narrow enough that two
# genuinely different posts sharing boilerplate caption text on the same
# account pair over a slow week don't get conflated.
DEDUP_TIMESTAMP_WINDOW_HOURS = 48


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_since(brand_id: str, posts: dict) -> datetime:
    """Earlier of (newest stored IG post, 10-day refresh cutoff). First pull
    for a brand with no history yet backfills config.INITIAL_PULL_DAYS
    (30) — not 90: a 90-day backfill across every brand at once is exactly
    what exhausted an entire month's Apify credit in one run. Every run
    after this one is purely incremental (since the newest stored post),
    so the store's real history keeps growing past 30 on its own; nothing
    ever gets re-pulled for a period already on file."""
    now = datetime.now(timezone.utc)
    refresh_cutoff = now - timedelta(days=config.REFETCH_DAYS)
    existing = [p for p in posts.get(brand_id, []) if p.get("platform") == "ig"]
    dates = [d for d in (parse_dt(p.get("posted_at")) for p in existing) if d]
    if not dates:
        return now - timedelta(days=config.INITIAL_PULL_DAYS)
    return min(max(dates), refresh_cutoff)


def _map_post_type(raw_type: str | None) -> str:
    t = (raw_type or "").lower()
    if t == "video":
        return "reel"
    if t == "sidecar":
        return "carousel"
    return "image"


def _extract_views(item: dict, post_type: str) -> int | None:
    """Static (image/carousel-without-video) posts have no view concept at
    all — this must stay `None`, never coerced to 0. The scraper only ever
    populates a view/play count field on actual video content."""
    if post_type == "image":
        return None
    for field in ("videoViewCount", "videoPlayCount", "viewsCount"):
        if item.get(field) is not None:
            return int(item[field])
    return None


def _is_restricted_item(item: dict) -> bool:
    """True for the single placeholder item Apify's actor returns in place
    of real posts when it can't reach a profile without a login — private
    accounts, and (the case that mattered for alcohol brands, and could in
    principle recur for any age/sensitive-content-gated account) Instagram's
    own content gate for a market. No Apify setting bypasses this; the actor
    is documented to never support login for any profile. Detecting this is
    what keeps a gated handle from silently reading as "posted once" instead
    of "unmeasurable"."""
    return bool(item.get("error") or item.get("errorDescription") or item.get("isRestrictedProfile"))


def _extract_followers(item: dict) -> int | None:
    """Best-effort: not every actor response version carries the owner's
    follower count on a post item, so this probes the field names known to
    appear before giving up — never fabricated, never guessed at a value."""
    for key in ("followersCount", "ownerFollowersCount"):
        val = item.get(key)
        if isinstance(val, int):
            return val
    owner = item.get("owner")
    if isinstance(owner, dict) and isinstance(owner.get("followersCount"), int):
        return owner["followersCount"]
    return None


def build_post_record(item: dict, handle: str) -> dict | None:
    external_id = item.get("id") or item.get("shortCode")
    if not external_id:
        return None
    post_type = _map_post_type(item.get("type"))
    return {
        "external_id": str(external_id),
        "handle": handle,
        "posted_at": item.get("timestamp"),
        "post_type": post_type,
        "caption": item.get("caption") or "",
        "media_url": item.get("url") or item.get("displayUrl") or item.get("videoUrl"),
        "views": _extract_views(item, post_type),
        "likes": item.get("likesCount"),
        "comments": item.get("commentsCount"),
    }


def _normalize_caption(caption: str | None) -> str:
    return " ".join((caption or "").split()).strip().lower()


def mark_cross_handle_duplicates(records: list[dict]) -> int:
    """Flags (does not drop) a record that's the same creative as another
    record from a *different* handle of the same brand — same normalized
    caption, posted within DEDUP_TIMESTAMP_WINDOW_HOURS of each other.
    Requires real, non-empty caption text on both sides: two blank-caption
    image posts matching on timestamp alone is too weak a signal and would
    risk merging genuinely different content. A no-op for any brand with
    only one handle. Returns the number of records flagged."""
    by_handle: dict[str, list[dict]] = {}
    for r in records:
        by_handle.setdefault(r["handle"], []).append(r)
    handles = list(by_handle.keys())
    flagged = 0
    for i in range(len(handles)):
        for j in range(i + 1, len(handles)):
            for a in by_handle[handles[i]]:
                if a.get("is_duplicate"):
                    continue
                cap_a = _normalize_caption(a.get("caption"))
                dt_a = parse_dt(a.get("posted_at"))
                if not cap_a or not dt_a:
                    continue
                for b in by_handle[handles[j]]:
                    if b.get("is_duplicate"):
                        continue
                    if _normalize_caption(b.get("caption")) != cap_a:
                        continue
                    dt_b = parse_dt(b.get("posted_at"))
                    if not dt_b or abs((dt_a - dt_b).total_seconds()) > DEDUP_TIMESTAMP_WINDOW_HOURS * 3600:
                        continue
                    b["is_duplicate"] = True
                    b["duplicate_of"] = a["external_id"]
                    flagged += 1
                    break
    return flagged


class ApifyQuotaExceeded(RuntimeError):
    """Apify returned 403 — the account's free/paid credit is exhausted for
    this billing period. Not retryable within this run: every remaining
    brand would 403 too, so the caller should stop attempting further
    brands rather than burn through each one individually to rediscover
    the same fact (RULE — a quota error is expected operationally, not a
    crash; the fix is to skip the rest of Instagram for this run, not to
    keep hammering a dead credit pool)."""


def call_apify(handle: str, since: datetime, token: str, actor: str = DEFAULT_ACTOR) -> list[dict]:
    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle.lstrip('@')}/"],
        "resultsType": "posts",
        "resultsLimit": RESULTS_LIMIT,
        "onlyPostsNewerThan": since.strftime("%Y-%m-%d"),
    }
    resp = requests.post(
        f"{APIFY_API}/acts/{actor}/run-sync-get-dataset-items",
        params={"token": token},
        json=run_input,
        timeout=300,
    )
    if resp.status_code == 403:
        raise ApifyQuotaExceeded(f"Apify quota exhausted (403) for handle={handle}: {resp.text[:300]}")
    if not resp.ok:
        raise RuntimeError(f"Apify actor run failed: {resp.status_code} {resp.text[:300]}")
    items = resp.json()
    usage.record_usage("pull_instagram", len(items))
    return items


def dry_run() -> None:
    posts = store.load_posts()
    print("[pull_instagram] DRY RUN — no network call, no credit spent, no store write")
    print(f"  month-to-date estimated Apify spend: ${usage.month_to_date_usd():.2f} "
          f"of ${config.APIFY_MONTHLY_CEILING_USD:.2f}")
    for brand_id, brand in config.BRANDS.items():
        handles = brand.get("handle_ig") or []
        if not handles:
            print(f"  {brand_id}: no handle_ig in config, will be skipped")
            continue
        since = compute_since(brand_id, posts)
        flag = "" if brand.get("verified") else "  ** UNVERIFIED — real run will refuse **"
        multi = f" ({len(handles)} handles, deduped on overlap)" if len(handles) > 1 else ""
        print(f"  {brand_id}: handles={handles} since={since:%Y-%m-%d} "
              f"limit={RESULTS_LIMIT}{multi}{flag}")


def run(token: str | None = None) -> str:
    unverified = config.unverified_brands()
    if unverified:
        started_at = finished_at = store.now_iso()
        error = f"refusing to run: unverified brands {unverified}"
        store.append_pull_log("pull_instagram", started_at, finished_at, 0, 0, "error", error)
        print(f"[pull_instagram] {error}", file=sys.stderr)
        return "error"

    token = token or os.environ.get("APIFY_TOKEN")
    started_at = store.now_iso()
    if not token:
        finished_at = store.now_iso()
        store.append_pull_log("pull_instagram", started_at, finished_at, 0, 0, "error", "APIFY_TOKEN not set")
        return "error"

    posts = store.load_posts()
    channel_stats = store.load_channel_stats()
    total_in = 0
    total_upserted = 0
    errors: list[str] = []
    warnings: list[str] = []
    skipped: list[str] = []
    brands_attempted = 0
    brands_succeeded = 0
    quota_exhausted = False
    cutoff90 = datetime.now(timezone.utc) - timedelta(days=90)

    for brand_id, brand in config.BRANDS.items():
        handles = brand.get("handle_ig") or []
        if not handles:
            # Empty list is an unresolved handle, not an error — skip and
            # log, never fail the run over it (config.py's module docstring).
            skipped.append(brand_id)
            print(f"[pull_instagram] {brand_id}: no handle_ig in config, skipping")
            continue
        if quota_exhausted:
            # Every remaining brand would 403 too — don't rediscover that
            # one brand at a time. Skip and log, not an error (RULE — a
            # quota error is expected operationally, not a crash).
            skipped.append(brand_id)
            print(f"[pull_instagram] {brand_id}: skipping — Apify credit exhausted this run")
            continue
        brands_attempted += 1
        try:
            since = compute_since(brand_id, posts)
            brand_records: list[dict] = []
            raw_item_count = 0
            restricted_item_count = 0
            followers_sum = 0
            followers_found = False

            for handle in handles:
                items = call_apify(handle, since, token)
                raw_item_count += len(items)
                # Raw, pre-filter, per handle — the diagnostic that actually
                # shows whether the actor paginated or came back thin,
                # independent of what survives filtering below.
                print(f"[pull_instagram] {brand_id}: apify returned {len(items)} raw item(s) "
                      f"for handle={handle} since={since:%Y-%m-%d} limit={RESULTS_LIMIT}")

                restricted_items = [i for i in items if _is_restricted_item(i)]
                restricted_item_count += len(restricted_items)
                if restricted_items:
                    detail = (restricted_items[0].get("errorDescription")
                              or restricted_items[0].get("error") or "restricted profile")
                    msg = (f"{brand_id}: Apify returned {len(restricted_items)} restricted/error item(s) "
                           f"for handle={handle} — {detail!r}. Instagram is very likely serving this "
                           f"handle's age/sensitive-content gate to the logged-out scraper; the actor "
                           f"cannot log in for any profile, so no input setting bypasses this. Treated "
                           f"as unmeasurable, not zero posts.")
                    warnings.append(msg)
                    print(f"[pull_instagram] WARN {msg}", file=sys.stderr)

                usable_items = [i for i in items if not _is_restricted_item(i)]
                brand_records += [r for r in (build_post_record(i, handle) for i in usable_items) if r is not None]

                for item in usable_items:
                    followers = _extract_followers(item)
                    if followers is not None:
                        followers_sum += followers
                        followers_found = True
                        break  # one confirmed follower count per handle is enough

            dup_count = mark_cross_handle_duplicates(brand_records) if len(handles) > 1 else 0
            if dup_count:
                print(f"[pull_instagram] {brand_id}: {dup_count} cross-handle duplicate(s) flagged "
                      f"(same creative posted to more than one of this brand's own handles) — kept in "
                      f"store with real engagement intact, excluded from post-count stats")

            rows_in, rows_new, rows_updated = store.upsert_posts(posts, brand_id, "ig", brand_records)
            total_in += rows_in
            total_upserted += rows_new + rows_updated
            print(f"[pull_instagram] {brand_id}: {rows_in} posts seen since {since:%Y-%m-%d} across "
                  f"{len(handles)} handle(s), {rows_new} new, {rows_updated} refreshed")

            if followers_found:
                channel_stats.setdefault(brand_id, {})["ig"] = {
                    "followers": followers_sum, "updated_at": store.now_iso(),
                }

            # Volume guard: a big brand reading as near-silent is much more
            # likely an under-fetch than a real posting gap — never let that
            # pass with no trace (see module docstring, failure mode 2).
            # Duplicates don't count toward "posted" — they're the same
            # content, not additional volume.
            recent_count = sum(
                1 for p in posts.get(brand_id, [])
                if p.get("platform") == "ig" and not p.get("is_duplicate")
                and (d := parse_dt(p.get("posted_at"))) and d >= cutoff90
            )
            if recent_count < VOLUME_GUARD_MIN_POSTS_90D:
                followers = ((channel_stats.get(brand_id, {}).get("ig") or {}).get("followers")
                             or brand.get("ig_followers_hint"))
                if followers is not None and followers > VOLUME_GUARD_FOLLOWER_FLOOR:
                    msg = (f"{brand_id}: only {recent_count} IG post(s) in the trailing 90 days despite "
                           f"~{followers} followers — raw_items_this_run={raw_item_count} "
                           f"restricted_items={restricted_item_count}. Likely an under-fetch, not a real "
                           f"posting gap.")
                    warnings.append(msg)
                    print(f"[pull_instagram] WARN {msg}", file=sys.stderr)
                elif followers is None:
                    print(f"[pull_instagram] {brand_id}: only {recent_count} IG post(s) in the trailing "
                          f"90 days and no follower count on file (scrape didn't carry one, and "
                          f"config.ig_followers_hint is unset) — can't run the volume guard to confirm "
                          f"this is genuine. Hand-fill ig_followers_hint in config.py once checked.")
            brands_succeeded += 1
        except ApifyQuotaExceeded as exc:
            quota_exhausted = True
            msg = f"{brand_id}: {exc}. Skipping remaining brands for this run — credit won't recover mid-run."
            warnings.append(msg)
            print(f"[pull_instagram] WARN {msg}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 — one brand's failure must not sink the whole run
            errors.append(f"{brand_id}: {exc}")
            print(f"[pull_instagram] ERROR {brand_id}: {exc}", file=sys.stderr)

    store.save_posts(posts)
    store.save_channel_stats(channel_stats)

    finished_at = store.now_iso()
    # A partial pull must commit what it got: only a brand-attempted run
    # where NOT ONE brand actually succeeded fails the workflow. A quota
    # 403 partway through, or one brand's transient error, is an expected
    # operational outcome, not a crash — everything already fetched this
    # run stays and gets committed.
    if brands_attempted > 0 and brands_succeeded == 0:
        status = "error"
    elif errors or warnings:
        status = "warn"
    else:
        status = "ok"

    error_text = "; ".join(errors + warnings) if (errors or warnings) else None
    store.append_pull_log("pull_instagram", started_at, finished_at, total_in, total_upserted, status, error_text)
    print(f"[pull_instagram] done: status={status} rows_in={total_in} rows_upserted={total_upserted} "
          f"brands_succeeded={brands_succeeded}/{brands_attempted} skipped={skipped} warnings={len(warnings)}")
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="preview what would be fetched, spend no credit")
    args = parser.parse_args()
    if args.dry_run:
        dry_run()
        sys.exit(0)
    run()
    # No expected outcome — "ok", "warn", or "error" (zero brands
    # succeeded, e.g. a dead token or total quota exhaustion) — ever exits
    # non-zero. Every one of those is a normal, logged operational state
    # (store.append_pull_log() above already recorded it), not a reason to
    # kill the workflow and skip build_data/commit. The only way this
    # process exits non-zero is an unhandled crash — a real bug, not
    # something this function decides.
    sys.exit(0)


if __name__ == "__main__":
    main()
