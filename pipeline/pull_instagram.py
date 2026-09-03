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
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

from . import config, store

APIFY_API = "https://api.apify.com/v2"
DEFAULT_ACTOR = "apify~instagram-scraper"
RESULTS_LIMIT = 200


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_since(brand_id: str, posts: dict) -> datetime:
    """Earlier of (newest stored IG post, 10-day refresh cutoff). First pull
    for a brand with no history yet backfills 90 days, matching the
    YouTube lookback so the two platforms start from a comparable window."""
    now = datetime.now(timezone.utc)
    refresh_cutoff = now - timedelta(days=config.INSTAGRAM_REFRESH_WINDOW_DAYS)
    existing = [p for p in posts.get(brand_id, []) if p.get("platform") == "ig"]
    dates = [d for d in (parse_dt(p.get("posted_at")) for p in existing) if d]
    if not dates:
        return now - timedelta(days=90)
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


def build_post_record(item: dict) -> dict | None:
    external_id = item.get("id") or item.get("shortCode")
    if not external_id:
        return None
    post_type = _map_post_type(item.get("type"))
    return {
        "external_id": str(external_id),
        "posted_at": item.get("timestamp"),
        "post_type": post_type,
        "caption": item.get("caption") or "",
        "media_url": item.get("url") or item.get("displayUrl") or item.get("videoUrl"),
        "views": _extract_views(item, post_type),
        "likes": item.get("likesCount"),
        "comments": item.get("commentsCount"),
    }


def call_apify(handles: list[str], since: datetime, token: str, actor: str = DEFAULT_ACTOR) -> list[dict]:
    run_input = {
        "directUrls": [f"https://www.instagram.com/{h.lstrip('@')}/" for h in handles],
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
    if not resp.ok:
        raise RuntimeError(f"Apify actor run failed: {resp.status_code} {resp.text[:300]}")
    return resp.json()


def dry_run() -> None:
    posts = store.load_posts()
    print("[pull_instagram] DRY RUN — no network call, no credit spent, no store write")
    for brand_id, brand in config.BRANDS.items():
        if not brand.get("handles_ig"):
            continue
        since = compute_since(brand_id, posts)
        flag = "" if brand.get("verified") else "  ** UNVERIFIED — real run will refuse **"
        print(f"  {brand_id}: handles={brand['handles_ig']} since={since:%Y-%m-%d} "
              f"limit={RESULTS_LIMIT}{flag}")


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
    total_in = 0
    total_upserted = 0
    errors: list[str] = []

    for brand_id, brand in config.BRANDS.items():
        handles = brand.get("handles_ig") or []
        if not handles:
            continue
        try:
            since = compute_since(brand_id, posts)
            items = call_apify(handles, since, token)
            records = [r for r in (build_post_record(i) for i in items) if r is not None]
            rows_in, rows_new, rows_updated = store.upsert_posts(posts, brand_id, "ig", records)
            total_in += rows_in
            total_upserted += rows_new + rows_updated
            print(f"[pull_instagram] {brand_id}: {rows_in} posts seen since {since:%Y-%m-%d}, "
                  f"{rows_new} new, {rows_updated} refreshed")
        except Exception as exc:  # noqa: BLE001 — one brand's failure must not sink the whole run
            errors.append(f"{brand_id}: {exc}")
            print(f"[pull_instagram] ERROR {brand_id}: {exc}", file=sys.stderr)

    store.save_posts(posts)

    finished_at = store.now_iso()
    if errors and total_upserted == 0:
        status = "error"
    elif total_upserted == 0 or errors:
        status = "warn"
    else:
        status = "ok"

    error_text = "; ".join(errors) if errors else None
    store.append_pull_log("pull_instagram", started_at, finished_at, total_in, total_upserted, status, error_text)
    print(f"[pull_instagram] done: status={status} rows_in={total_in} rows_upserted={total_upserted}")
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="preview what would be fetched, spend no credit")
    args = parser.parse_args()
    if args.dry_run:
        dry_run()
        sys.exit(0)
    status = run()
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
