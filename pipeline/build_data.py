"""
build_data.py — Phase 4a/4c/4d.

Reads the store, emits public/ci/data.json in exactly the shape the
dashboard's `init()` expects (see Phase 4e). Also writes a dated copy to
store/snapshots/ — that folder is the rollback mechanism in a no-database
stack: a bad run's snapshot just doesn't get copied over data.json (see
RULE 7).

Paid/organic split is a statistical estimate, not a classification: a post's
views against the trailing-90-day median for its own brand/platform/type.
Everything here is public-data arithmetic; nothing needs an LLM. That's
Phase 5.

`untracked` is computed from config.UNTRACKED["share_assumption"] — a
stated, MODELLED tail share, not a measurement. Each window's untracked value
is solved so that untracked / (tracked_total + untracked) == share_assumption
for that window's tracked total, so the assumption reads consistently at
every range. This is a placeholder until a wider market estimate exists —
flagged MODELLED tier at render time exactly like everything else derived
from an assumption rather than a raw count.
"""

from __future__ import annotations

import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import config, run_summary, store

IST = timezone(timedelta(hours=5, minutes=30))
SERIES_BUCKETS = 6
SERIES_WINDOW_DAYS = 30
VISIBILITY_TYPES = {"video", "reel"}
STATIC_TYPES = {"image", "carousel"}


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def median_baselines(posts: list[dict], now: datetime) -> dict[str, float]:
    """Median views per post_type over the trailing config.BASELINE_DAYS —
    the baseline that estimate_paid_organic() compares each post against.
    Needs no special-casing for a brand with less history than that: the
    cutoff just doesn't exclude anything yet, and the median is computed
    over whatever's actually on file (see compute_baseline_days_actual for
    how much that actually is)."""
    cutoff = now - timedelta(days=config.BASELINE_DAYS)
    by_type: dict[str, list[int]] = {}
    for p in posts:
        if p.get("views") is None:
            continue
        posted = parse_dt(p.get("posted_at"))
        if not posted or posted < cutoff:
            continue
        by_type.setdefault(p["post_type"], []).append(p["views"])
    return {t: statistics.median(v) for t, v in by_type.items()}


def compute_baseline_days_actual(posts_by_platform: dict[str, list[dict]], now: datetime) -> int:
    """How many days of real trailing history actually back this brand's
    paid/organic baseline, capped at config.BASELINE_DAYS. The binding
    constraint is whichever TRACKED platform (one this brand actually has
    a handle for and has ever been pulled) has the least history — a
    platform this brand doesn't track at all doesn't drag the number down.
    Right after a brand's first-ever Instagram pull this is ~30
    (config.INITIAL_PULL_DAYS), not 90; it grows on its own as the
    incremental pulls accumulate. Exposed per brand (meta.profiles.*
    .baselineDaysActual) so the anomaly split's confidence is visible
    instead of silently assumed to always rest on a full window."""
    ages = []
    for posts in posts_by_platform.values():
        dates = [d for d in (parse_dt(p.get("posted_at")) for p in posts) if d]
        if dates:
            ages.append((now - min(dates)).days)
    if not ages:
        return 0
    return max(0, min(config.BASELINE_DAYS, min(ages)))


def estimate_paid_organic(views: int, baseline: float | None) -> tuple[int, int]:
    if baseline is None or baseline <= 0:
        # not enough trailing history to have an opinion yet — call it organic
        return 0, views
    if views > baseline * config.ANOMALY_THRESHOLD:
        paid = round(views - baseline)
        return paid, round(baseline)
    return 0, views


def in_window(dt: datetime | None, start: datetime, end: datetime) -> bool:
    return bool(dt) and start <= dt <= end


def aggregate_window(posts: list[dict], start: datetime, end: datetime,
                      baselines: dict[str, float], followers: int | None) -> dict:
    organic = 0
    paid = 0
    n_posts = 0
    for p in posts:
        posted = parse_dt(p.get("posted_at"))
        if not in_window(posted, start, end):
            continue
        # A cross-handle duplicate (same creative, two of a brand's own
        # accounts — pull_instagram.py's McDonald's case) is real, separate
        # engagement from two real audiences, so its views still count
        # toward visibility in full; it just isn't a second piece of
        # content, so it doesn't add a second post to the volume count.
        if not p.get("is_duplicate"):
            n_posts += 1
        if p.get("views") is None:
            continue  # static: counts toward volume, not visibility (RULE 3)
        paid_est, organic_est = estimate_paid_organic(p["views"], baselines.get(p["post_type"]))
        organic += organic_est
        paid += paid_est
    return {"organic": organic, "paid": paid, "followers": followers, "posts": n_posts}


def compute_format_mix(posts_90d: list[dict]) -> str:
    # Cross-handle duplicates excluded — this is a distribution over unique
    # content, not over raw post rows (see aggregate_window).
    posts_90d = [p for p in posts_90d if not p.get("is_duplicate")]
    video = sum(1 for p in posts_90d if p["post_type"] in VISIBILITY_TYPES)
    static = sum(1 for p in posts_90d if p["post_type"] in STATIC_TYPES)
    total = video + static
    if total == 0:
        return "mixed"
    ratio = video / total
    if ratio > 0.6:
        return "video"
    if ratio < 0.3:
        return "static"
    return "mixed"


def compute_vehicle_mix(posts: list[dict], start: datetime, end: datetime) -> dict[str, float]:
    counts: Counter = Counter()
    total = 0
    for p in posts:
        if p.get("is_duplicate"):
            continue  # same creative as another of the brand's own posts — not a second data point
        if not in_window(parse_dt(p.get("posted_at")), start, end):
            continue
        counts[p.get("vehicle") or "unclassified"] += 1
        total += 1
    if total == 0:
        return {v: 0.0 for v in config.VEHICLES}
    return {v: round(counts.get(v, 0) / total, 4) for v in config.VEHICLES}


def compute_engagement30(posts: list[dict], start: datetime, end: datetime, is_client: bool,
                          client_insights: dict) -> dict:
    likes = 0
    comments = 0
    for p in posts:
        if not in_window(parse_dt(p.get("posted_at")), start, end):
            continue
        likes += p.get("likes") or 0
        comments += p.get("comments") or 0
    # Shares/saves aren't exposed by any public-data source this pipeline
    # touches (Apify's public IG scrape has no share/save count; YouTube has
    # no "save" concept) — structurally null for every competitor, forever.
    # The client can fill their own from Meta Business Suite Insights (an
    # authenticated source no scraper here has) by hand-editing
    # store/client_insights.json; nothing pulls or overwrites that file
    # automatically. Everyone else stays null per RULE 3 — never a zero.
    shares = client_insights.get("shares") if is_client else None
    saves = client_insights.get("saves") if is_client else None
    return {"likes": likes, "comments": comments, "shares": shares, "saves": saves}


def compute_series(posts: list[dict], baselines: dict[str, float], now: datetime) -> list[float]:
    start = now - timedelta(days=SERIES_WINDOW_DAYS)
    bucket_len = timedelta(days=SERIES_WINDOW_DAYS / SERIES_BUCKETS)
    sums = [0.0] * SERIES_BUCKETS
    for p in posts:
        if p.get("views") is None:
            continue
        posted = parse_dt(p.get("posted_at"))
        if not posted or posted < start or posted > now:
            continue
        idx = min(SERIES_BUCKETS - 1, int((posted - start) / bucket_len))
        paid_est, organic_est = estimate_paid_organic(p["views"], baselines.get(p["post_type"]))
        sums[idx] += paid_est + organic_est
    mean = sum(sums) / SERIES_BUCKETS
    if mean == 0:
        return [0.0] * SERIES_BUCKETS
    return [round(s / mean, 3) for s in sums]


def compute_comment_stats(brand_id: str, comments_store: dict, now: datetime) -> tuple[dict, float, dict, dict]:
    recs = comments_store.get(brand_id, [])
    win_start = now - timedelta(days=30)
    prev_start, prev_end = now - timedelta(days=60), now - timedelta(days=30)

    def clean(items):
        return [c for c in items if not c.get("spam") and c.get("polarity")]

    cur_all = [c for c in recs if in_window(parse_dt(c.get("posted_at")), win_start, now)]
    prev_all = [c for c in recs if in_window(parse_dt(c.get("posted_at")), prev_start, prev_end)]
    cur = clean(cur_all)
    prev = clean(prev_all)

    def polarity_shares(items):
        n = len(items)
        if n == 0:
            return {"pos": 0.0, "neu": 0.0, "neg": 0.0}
        return {
            "pos": round(sum(1 for c in items if c["polarity"] == "pos") / n, 3),
            "neu": round(sum(1 for c in items if c["polarity"] == "neu") / n, 3),
            "neg": round(sum(1 for c in items if c["polarity"] == "neg") / n, 3),
        }

    sentiment = polarity_shares(cur)
    prev_sentiment = polarity_shares(prev)
    neg_delta_pp = round((sentiment["neg"] - prev_sentiment["neg"]) * 100, 1)

    theme_counts = Counter(c["theme"] for c in cur if c.get("theme"))
    total_themed = sum(theme_counts.values())
    theme_share = {
        t: (round(theme_counts.get(t, 0) / total_themed, 3) if total_themed else 0.0)
        for t in config.THEMES
    }

    spam_total = sum(1 for c in cur_all if c.get("spam"))
    n_total = len(cur_all)
    spam_rate = round(spam_total / n_total, 3) if n_total else config.SPAM_RATE_BASE
    comment_sample = {"n": n_total, "spamRate": spam_rate}

    return sentiment, neg_delta_pp, theme_share, comment_sample


def compute_meta_comment_sample(comments_store: dict, now: datetime) -> dict:
    """Top-level composition across every brand's current-window sample —
    "n = X · YT 70% / IG 30%" on the dashboard. YT/IG are sampled at very
    different depths (config.YT_COMMENT_POSTS/PER_POST vs IG_COMMENT_POSTS/
    PER_POST, Phase 2), so a sample whose platform mix is invisible can't be
    trusted; this is what makes that mix visible."""
    win_start = now - timedelta(days=30)
    all_recs = []
    for recs in comments_store.values():
        all_recs.extend(c for c in recs if in_window(parse_dt(c.get("posted_at")), win_start, now))
    n_total = len(all_recs)
    if n_total == 0:
        return {"n": 0, "spamRate": config.SPAM_RATE_BASE, "ytShare": 0.0, "igShare": 0.0}
    spam_rate = round(sum(1 for c in all_recs if c.get("spam")) / n_total, 3)
    yt_share = round(sum(1 for c in all_recs if c.get("platform") == "yt") / n_total, 3)
    ig_share = round(sum(1 for c in all_recs if c.get("platform") == "ig") / n_total, 3)
    return {"n": n_total, "spamRate": spam_rate, "ytShare": yt_share, "igShare": ig_share}


def build_profile(brand_id: str, brand: dict, posts: dict, channel_stats: dict,
                   comments_store: dict, trends: dict, now: datetime, client_insights: dict,
                   coverage_days: int) -> dict:
    ig_posts = [p for p in posts.get(brand_id, []) if p.get("platform") == "ig"]
    yt_posts = [p for p in posts.get(brand_id, []) if p.get("platform") == "yt"]

    ig_baselines = median_baselines(ig_posts, now)
    yt_baselines = median_baselines(yt_posts, now)
    ig_followers = (channel_stats.get(brand_id, {}).get("ig") or {}).get("followers")
    yt_followers = (channel_stats.get(brand_id, {}).get("yt") or {}).get("followers")
    baseline_days_actual = compute_baseline_days_actual({"ig": ig_posts, "yt": yt_posts}, now)

    windows = {}
    for label, days in (("7", 7), ("30", 30), ("90", 90)):
        # A window longer than the store's real coverage isn't a small
        # number, it's a wrong one — computing "90 days" from 30 days of
        # actual history silently understates it rather than admitting the
        # window can't be answered yet. Null, not zero (RULE — same
        # null-vs-zero convention as shares/saves, static-post views,
        # below-threshold Trends). The front end never lets a range this
        # long even be selected while coverageDays is short (meta.
        # coverageDays gates it), so this is a safety net, not the primary
        # guard.
        if days > coverage_days:
            windows[label] = None
            continue
        start = now - timedelta(days=days)
        windows[label] = {
            "ig": aggregate_window(ig_posts, start, now, ig_baselines, ig_followers),
            "yt": aggregate_window(yt_posts, start, now, yt_baselines, yt_followers),
        }

    prev_start, prev_end = now - timedelta(days=60), now - timedelta(days=30)
    prev30 = {
        "ig": aggregate_window(ig_posts, prev_start, prev_end, ig_baselines, ig_followers),
        "yt": aggregate_window(yt_posts, prev_start, prev_end, yt_baselines, yt_followers),
    }

    cutoff90 = now - timedelta(days=90)
    recent = [p for p in ig_posts + yt_posts if in_window(parse_dt(p.get("posted_at")), cutoff90, now)]
    format_mix = compute_format_mix(recent)

    win30_start = now - timedelta(days=30)
    all_posts = ig_posts + yt_posts
    vehicle_mix = compute_vehicle_mix(all_posts, win30_start, now)
    vehicle_prev_mix = compute_vehicle_mix(all_posts, prev_start, prev_end)

    engagement30 = compute_engagement30(all_posts, win30_start, now, brand.get("is_client", False),
                                         client_insights)

    series_ig = compute_series(ig_posts, ig_baselines, now)
    series_yt = compute_series(yt_posts, yt_baselines, now)

    sentiment, neg_delta_pp, theme_share, comment_sample = compute_comment_stats(brand_id, comments_store, now)

    # No trends.json entry yet (pull_trends.py hasn't run) is the same "no
    # real number" case as a below-threshold bucket — None throughout, not
    # a flat 0 line the front end would draw as measured zero interest.
    search = (trends.get(brand_id) or {}).get("series") or [None] * 6

    return {
        "windows": windows,
        "prev30": prev30,
        "formatMix": format_mix,
        "vehicleMix": vehicle_mix,
        "vehiclePrevMix": vehicle_prev_mix,
        "sentiment": sentiment,
        "negDeltaPP": neg_delta_pp,
        "themeShare": theme_share,
        "engagement30": engagement30,
        "search": search,
        "seriesIG": series_ig,
        "seriesYT": series_yt,
        "commentSample": comment_sample,
        "baselineDaysActual": baseline_days_actual,
    }


def _as_list(val) -> list:
    """handle_fb is a plain string for every brand except McDonald's (two
    franchise operators, two pages) — normalize either shape rather than
    assuming one."""
    if val is None:
        return []
    return list(val) if isinstance(val, list) else [val]


def build_meta(now: datetime, comments_store: dict, coverage_days: int, tracking_since: str | None,
               sources: dict) -> dict:
    handles = {
        bid: {"ig": [f"@{h}" for h in b.get("handle_ig") or []],
              "yt": b.get("yt_handle"), "fb": _as_list(b.get("handle_fb"))}
        for bid, b in config.BRANDS.items()
    }
    trends_queries = {bid: b["trends_query"] for bid, b in config.BRANDS.items()}
    return {
        "updated": now.astimezone(IST).strftime("%d %b %H:%M IST").upper(),
        # Machine-readable companion to `updated` — the front end's staleness
        # guard (Phase 4e-iv) needs an unambiguous instant to diff against;
        # the pretty IST string above has no year and isn't meant for parsing.
        "updatedISO": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spamRateBase": config.SPAM_RATE_BASE,
        "handles": handles,
        "trendsQueries": trends_queries,
        "anomalyThreshold": config.ANOMALY_THRESHOLD,
        # How much real trailing history the store has, whole-pipeline —
        # gates which range presets (7/30/90) the front end lets you pick.
        # Never assumed to be the full 90 until it demonstrably is; see
        # compute_coverage().
        "coverageDays": coverage_days,
        "trackingSince": tracking_since,
        # Per-source degradation, surfaced so a down source is information
        # for a viewer, not a reason this pipeline published nothing — see
        # compute_sources().
        "sources": sources,
        "untrackedShareAssumption": config.UNTRACKED["share_assumption"],
        "commentSample": compute_meta_comment_sample(comments_store, now),
        "excluded": dict(config.EXCLUDED),
        "logoSvg": config.LOGO_SVG,
        # Every category-facing string a render function needs lives here,
        # never hardcoded in index.html — a category pivot (alcobev -> QSR,
        # or whatever's next) is a config.LABELS edit, not a find-and-replace
        # across render functions.
        "labels": dict(config.LABELS),
        # Same for the taxonomy itself — id, display label, color, and (for
        # themes) the negativity-weighting constant all come from config,
        # never a hardcoded JS array.
        "vehicles": [
            {"id": v, "label": config.VEHICLE_LABELS[v], "color": _css_var(config.VEHICLE_COLOR_VARS[v])}
            for v in config.VEHICLES
        ],
        "themes": [
            {"id": t, "label": config.THEME_LABELS[t], "lift": config.THEME_LIFT[t],
             "outlierCaption": config.THEME_OUTLIER_CAPTIONS[t]}
            for t in config.THEMES
        ],
        **config.META_STRINGS,
    }


def _css_var(name: str) -> str:
    return f"var({name})"


def compute_coverage(posts: dict, now: datetime) -> tuple[int, str | None]:
    """How many days of real history the store has, capped at
    config.BASELINE_DAYS — the earliest posted_at across every platform
    and brand combined, not whichever single platform happens to be
    thinnest. A platform with no data yet (Instagram mid quota-exhaustion,
    a brand-new handle, whatever) simply contributes nothing to this span;
    it must never drag a platform that DOES have real history down to
    near-zero and blank the whole dashboard behind it — a brand should be
    viewable off the platform(s) that have data even when another has
    none. Once established this only ever moves earlier (more backfill
    surfacing older posts) or stays the same as runs accumulate, never
    later — so it can't suddenly regress just because a previously-empty
    platform starts (or resumes) contributing a handful of recent posts.
    Returns (coverage_days, tracking_since as YYYY-MM-DD, or None if the
    store has no posts at all yet)."""
    earliest: datetime | None = None
    for records in posts.values():
        for p in records:
            posted = parse_dt(p.get("posted_at"))
            if not posted:
                continue
            if earliest is None or posted < earliest:
                earliest = posted
    if earliest is None:
        return 0, None
    coverage_days = max(0, min(config.BASELINE_DAYS, (now - earliest).days))
    return coverage_days, earliest.strftime("%Y-%m-%d")


def _pull_status(entry: dict | None, no_handles: bool) -> dict:
    """One platform's degradation status for meta.sources — 'a down
    source is information for the viewer, not a reason to publish
    nothing.' Every pull script already exits 0 and logs its real outcome
    to pull_log.json regardless of what happened (see pull_youtube.py/
    pull_instagram.py's own main()); this just reads the same row a human
    would read in the Actions run summary (run_summary.py) and turns it
    into a status a render function can key off without parsing error
    text itself."""
    if no_handles:
        return {"status": "no_handle", "detail": "no brand has a handle configured for this platform",
                "lastRun": None, "rowsUpserted": None}
    if entry is None:
        return {"status": "never_run", "detail": None, "lastRun": None, "rowsUpserted": None}
    error = entry.get("error") or ""
    if entry["status"] == "ok":
        status = "ok"
    elif "quota" in error.lower() or " 403" in error or "hard limit" in error.lower():
        status = "quota_exhausted"
    else:
        status = "degraded"
    return {"status": status, "detail": entry.get("error"), "lastRun": entry.get("finished_at"),
            "rowsUpserted": entry.get("rows_upserted")}


def compute_sources(pull_log: list, posts: dict, comments_store: dict) -> dict:
    """meta.sources — youtube/instagram/classification, each with a status
    (ok / quota_exhausted / no_handle / never_run / degraded, or
    unclassified for classification) plus enough detail to explain it. A
    fresh deploy or a total outage across every source still builds and
    publishes data.json (RULE — see pipeline/README.md's "no pull or
    classify script exits non-zero" section); this is how that
    degradation reaches a viewer instead of just a CI log nobody but the
    pipeline's own operator ever reads."""
    latest = run_summary.latest_entries(pull_log)
    yt_no_handles = all(not b.get("yt_handle") for b in config.BRANDS.values())
    ig_no_handles = all(not b.get("handle_ig") for b in config.BRANDS.values())

    pending_posts = sum(1 for records in posts.values() for r in records
                         if r.get("model_version") != config.CURRENT_MODEL_VERSION)
    pending_comments = sum(1 for records in comments_store.values() for c in records
                            if c.get("model_version") != config.CURRENT_MODEL_VERSION)
    classify_entries = [latest.get("classify_posts"), latest.get("classify_comments")]
    classify_errors = [e.get("error") for e in classify_entries if e and e.get("error")]
    last_classify_run = max((e["finished_at"] for e in classify_entries if e), default=None)
    if pending_posts == 0 and pending_comments == 0:
        classification = {"status": "ok", "detail": None, "lastRun": last_classify_run,
                           "pendingPosts": 0, "pendingComments": 0}
    else:
        classification = {
            "status": "unclassified",
            "detail": f"{pending_posts} post(s), {pending_comments} comment(s) awaiting classification"
                       + (" — " + "; ".join(classify_errors)[:200] if classify_errors else ""),
            "lastRun": last_classify_run, "pendingPosts": pending_posts, "pendingComments": pending_comments,
        }

    return {
        "youtube": _pull_status(latest.get("pull_youtube"), yt_no_handles),
        "instagram": _pull_status(latest.get("pull_instagram"), ig_no_handles),
        "classification": classification,
    }


def compute_untracked(profiles_out: dict, coverage_days: int) -> dict:
    """Solve each window's untracked value so that
    untracked / (tracked_total + untracked) == share_assumption for that
    window's own tracked total — a stated, disclosed MODELLED figure, not a
    measurement (see module docstring). No per-platform breakdown exists for
    a bucket nothing is actually scraped from, so the whole modelled value
    is carried on `ig.organic`; `yt` stays zero rather than an arbitrary split.
    A window null across every brand (uncovered — see build_profile) stays
    null here too: a modelled share of an unanswerable number is itself
    unanswerable, not zero."""
    share = config.UNTRACKED["share_assumption"]

    def tracked_total(getter):
        total = 0
        for p in profiles_out.values():
            w = getter(p)
            if w is None:
                continue
            total += w["ig"]["organic"] + w["ig"]["paid"] + w["yt"]["organic"] + w["yt"]["paid"]
        return total

    def solve(total: float) -> int:
        return round(total * share / (1 - share)) if total else 0

    windows_out = {}
    for label, days in (("7", 7), ("30", 30), ("90", 90)):
        if days > coverage_days:
            windows_out[label] = None
            continue
        val = solve(tracked_total(lambda p, l=label: p["windows"][l]))
        windows_out[label] = {"ig": {"organic": val, "paid": 0}, "yt": {"organic": 0, "paid": 0}}
    prev_val = solve(tracked_total(lambda p: p["prev30"]))
    prev30_out = {"ig": {"organic": prev_val, "paid": 0}, "yt": {"organic": 0, "paid": 0}}
    return {
        "id": config.UNTRACKED["id"], "name": config.UNTRACKED["name"],
        "color": _css_var(config.UNTRACKED["color_var"]),
        "windows": windows_out, "prev30": prev30_out,
    }


def build() -> dict:
    now = datetime.now(timezone.utc)
    posts = store.load_posts()
    channel_stats = store.load_channel_stats()
    comments_store = store.load_comments()
    trends = store.load_json(config.TRENDS_PATH, {})
    client_insights_all = store.load_json(config.CLIENT_INSIGHTS_PATH, {})
    pull_log = store.load_json(config.PULL_LOG_PATH, [])
    coverage_days, tracking_since = compute_coverage(posts, now)
    sources = compute_sources(pull_log, posts, comments_store)

    brands_out = {
        bid: {
            "name": b["name"], "parent": b["parent"], "color": _css_var(b["color_var"]),
            "isClient": b.get("is_client", False),
            "handleIG": " / ".join(f"@{h}" for h in b.get("handle_ig") or []) or None,
            "handleYT": b.get("yt_handle"),
            "dormantSince": b.get("dormant_since"),
        }
        for bid, b in config.BRANDS.items()
    }
    portfolios_out = {
        pid: {"name": p["name"], "members": p["members"], "color": _css_var(p["color_var"]),
              **({"isClient": True} if p.get("is_client") else {})}
        for pid, p in config.PORTFOLIOS.items()
    }

    profiles_out = {
        bid: build_profile(bid, b, posts, channel_stats, comments_store, trends, now,
                            client_insights_all.get(bid, {}), coverage_days)
        for bid, b in config.BRANDS.items()
    }
    untracked_out = compute_untracked(profiles_out, coverage_days)

    return {
        "meta": build_meta(now, comments_store, coverage_days, tracking_since, sources),
        "brands": brands_out,
        "portfolios": portfolios_out,
        "untracked": untracked_out,
        "profiles": profiles_out,
    }


def validate(data: dict) -> list[str]:
    """A failed run must never overwrite a good data.json (RULE 7) — this is
    the gate that decides "failed". Deliberately conservative: structure and
    presence, not freshness (staleness is the front end's job per 4e-iv)."""
    problems = []
    if not data.get("meta", {}).get("updated"):
        problems.append("meta.updated missing")
    coverage_days = data.get("meta", {}).get("coverageDays", 0)
    for bid in config.BRANDS:
        prof = data.get("profiles", {}).get(bid)
        if not prof:
            problems.append(f"profiles.{bid} missing")
            continue
        for w, days in (("7", 7), ("30", 30), ("90", 90)):
            win = prof.get("windows", {}).get(w, "__missing__")
            if win == "__missing__":
                problems.append(f"profiles.{bid}.windows.{w} missing entirely")
            elif win is None:
                # Legitimately unavailable (coverage doesn't reach this
                # window yet) — null, not a validation failure. Only a
                # problem if coverage says it SHOULD have been computable.
                if days <= coverage_days:
                    problems.append(f"profiles.{bid}.windows.{w} is null despite coverageDays={coverage_days}")
            elif "ig" not in win or "yt" not in win:
                problems.append(f"profiles.{bid}.windows.{w} incomplete")
        if "prev30" not in prof:
            problems.append(f"profiles.{bid}.prev30 missing")
    # Trends caps a query at 100 chars including the "+" joins (Phase 5) — a
    # query over that limit doesn't error, it silently truncates and returns
    # garbage, which is worse than failing loudly here first.
    for bid, b in config.BRANDS.items():
        q = b.get("trends_query", "")
        if len(q) > 100:
            problems.append(f"BRANDS.{bid}.trends_query is {len(q)} chars, over Trends' 100-char cap: {q!r}")
    return problems


def main() -> None:
    data = build()
    problems = validate(data)
    if problems:
        print("[build_data] REFUSING TO PUBLISH — validation failed:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    store.save_json(config.DATA_JSON_PATH, data)
    snapshot_name = datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".json"
    store.save_json(config.SNAPSHOTS_DIR / snapshot_name, data)
    print(f"[build_data] wrote {config.DATA_JSON_PATH} and snapshot {snapshot_name}")
    print(f"[build_data] updated={data['meta']['updated']} brands={len(data['profiles'])}")


if __name__ == "__main__":
    main()
