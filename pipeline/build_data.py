"""
build_data.py — Phase 4a/4c/4d.

Reads the store, emits public/ci/data.json in exactly the shape the
dashboard's `init()` expects (see Phase 4e / brand/kingfisher-competitive-
intelligence.html). Also writes a dated copy to store/snapshots/ — that
folder is the rollback mechanism in a no-database stack: a bad run's
snapshot just doesn't get copied over data.json (see RULE 7).

Paid/organic split is a statistical estimate, not a classification: a post's
views against the trailing-90-day median for its own brand/platform/type.
Everything here is public-data arithmetic; nothing needs an LLM. That's
Phase 5.

`untracked` is left with EMPTY per-window objects, deliberately — this
pipeline only ever measures the eight named competitors. Fabricating a tail
percentage for brands never scraped would be exactly the "falsely confident
bar" the brief spends a whole section warning against, so the honest output
is nothing measured, and the front end (Phase 4e rewiring) treats a missing
untracked window as a zero contribution rather than crashing on it.
"""

from __future__ import annotations

import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import config, store

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
    """Median views per post_type over the trailing 90 days — the baseline
    that estimate_paid_organic() compares each post against."""
    cutoff = now - timedelta(days=90)
    by_type: dict[str, list[int]] = {}
    for p in posts:
        if p.get("views") is None:
            continue
        posted = parse_dt(p.get("posted_at"))
        if not posted or posted < cutoff:
            continue
        by_type.setdefault(p["post_type"], []).append(p["views"])
    return {t: statistics.median(v) for t, v in by_type.items()}


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
        n_posts += 1
        if p.get("views") is None:
            continue  # static: counts toward volume, not visibility (RULE 3)
        paid_est, organic_est = estimate_paid_organic(p["views"], baselines.get(p["post_type"]))
        organic += organic_est
        paid += paid_est
    return {"organic": organic, "paid": paid, "followers": followers, "posts": n_posts}


def compute_format_mix(posts_90d: list[dict]) -> str:
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
        if not in_window(parse_dt(p.get("posted_at")), start, end):
            continue
        counts[p.get("vehicle") or "unclassified"] += 1
        total += 1
    if total == 0:
        return {v: 0.0 for v in config.VEHICLES}
    return {v: round(counts.get(v, 0) / total, 4) for v in config.VEHICLES}


def compute_engagement30(posts: list[dict], start: datetime, end: datetime, is_client: bool) -> dict:
    likes = 0
    comments = 0
    for p in posts:
        if not in_window(parse_dt(p.get("posted_at")), start, end):
            continue
        likes += p.get("likes") or 0
        comments += p.get("comments") or 0
    # Shares/saves aren't exposed by any public-data source this pipeline
    # touches (Apify's public IG scrape has no share/save count; YouTube has
    # no "save" concept) — null for every brand, client included, per RULE 3:
    # this is a structural gap, not a zero.
    return {"likes": likes, "comments": comments, "shares": None, "saves": None}


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


def build_profile(brand_id: str, brand: dict, posts: dict, channel_stats: dict,
                   comments_store: dict, trends: dict, now: datetime) -> dict:
    ig_posts = [p for p in posts.get(brand_id, []) if p.get("platform") == "ig"]
    yt_posts = [p for p in posts.get(brand_id, []) if p.get("platform") == "yt"]

    ig_baselines = median_baselines(ig_posts, now)
    yt_baselines = median_baselines(yt_posts, now)
    ig_followers = (channel_stats.get(brand_id, {}).get("ig") or {}).get("followers")
    yt_followers = (channel_stats.get(brand_id, {}).get("yt") or {}).get("followers")

    windows = {}
    for label, days in (("7", 7), ("30", 30), ("90", 90)):
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

    engagement30 = compute_engagement30(all_posts, win30_start, now, brand.get("is_client", False))

    series_ig = compute_series(ig_posts, ig_baselines, now)
    series_yt = compute_series(yt_posts, yt_baselines, now)

    sentiment, neg_delta_pp, theme_share, comment_sample = compute_comment_stats(brand_id, comments_store, now)

    search = (trends.get(brand_id) or {}).get("series") or [0, 0, 0, 0, 0, 0]

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
    }


def build_meta(now: datetime) -> dict:
    handles = {
        bid: {"ig": [f"@{h}" for h in b["handles_ig"]], "yt": b.get("yt_handle") or b.get("name")}
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
        "logoSvg": config.LOGO_SVG,
        **config.META_STRINGS,
    }


def build() -> dict:
    now = datetime.now(timezone.utc)
    posts = store.load_posts()
    channel_stats = store.load_channel_stats()
    comments_store = store.load_comments()
    trends = store.load_json(config.TRENDS_PATH, {})

    brands_out = {
        bid: {
            "name": b["name"], "parent": b["parent"], "color": b["color"],
            "isClient": b.get("is_client", False),
            "handleIG": f"@{b['handles_ig'][0]}" if b.get("handles_ig") else None,
            "handleYT": b.get("yt_handle"),
        }
        for bid, b in config.BRANDS.items()
    }
    portfolios_out = {
        pid: {"name": p["name"], "members": p["members"], "color": p["color"], **({"isClient": True} if p.get("is_client") else {})}
        for pid, p in config.PORTFOLIOS.items()
    }
    untracked_out = {
        "id": config.UNTRACKED["id"], "name": config.UNTRACKED["name"], "color": config.UNTRACKED["color"],
        "windows": {"7": {}, "30": {}, "90": {}}, "prev30": {},
    }

    profiles_out = {
        bid: build_profile(bid, b, posts, channel_stats, comments_store, trends, now)
        for bid, b in config.BRANDS.items()
    }

    return {
        "meta": build_meta(now),
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
    for bid in config.BRANDS:
        prof = data.get("profiles", {}).get(bid)
        if not prof:
            problems.append(f"profiles.{bid} missing")
            continue
        for w in ("7", "30", "90"):
            win = prof.get("windows", {}).get(w)
            if not win or "ig" not in win or "yt" not in win:
                problems.append(f"profiles.{bid}.windows.{w} incomplete")
        if "prev30" not in prof:
            problems.append(f"profiles.{bid}.prev30 missing")
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
