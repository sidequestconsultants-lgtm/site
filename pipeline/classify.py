"""
classify.py — Phase 5. Gemini Flash free tier; caption sorting and comment
tagging don't need a frontier model.

Two independent jobs, both idempotent by model_version:

  classify_posts()    — vehicle classification (soda/nonalc/music/merch/
                         direct/unclassified) from caption + post_type, for
                         every raw_post that doesn't yet have a result at the
                         CURRENT_MODEL_VERSION. Confidence < 0.7 is forced to
                         'unclassified' — never guessed into a bucket.

  classify_comments() — samples top posts per brand by engagement and fetches
                         their comments, asymmetrically: YouTube (free within
                         quota) gets the top 25 posts × 200 comments each via
                         commentThreads.list; Instagram (Apify credit shared
                         with pull_instagram.py's post scraping) gets a much
                         thinner 8 posts × 100 comments, and stops fetching
                         entirely once the month's estimated Apify spend
                         (usage.py) crosses config.APIFY_MONTHLY_CEILING_USD —
                         post ingestion always has priority (RULE 7). Then
                         classifies spam / polarity / theme / language on the
                         survivors. Comments are heavily Hinglish and
                         code-mixed, which is the whole reason this is an LLM
                         pass and not a classical sentiment model.

Nothing here stores a comment author/username — see RULE in Phase 1.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

import requests

from . import config, store, usage

GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_API = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
CURRENT_MODEL_VERSION = f"{GEMINI_MODEL}-classify-v1"
POST_BATCH_SIZE = 20
# Asymmetric comment sampling (Phase 2 of the go-live prompt): YouTube
# commentThreads is free within quota, sample generously; Instagram costs
# Apify credit shared with post ingestion, sample much thinner and gate it
# behind the monthly spend ceiling (see usage.py). Both live in config.py.

VEHICLE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "vehicle": {"type": "STRING", "enum": config.VEHICLES},
            "confidence": {"type": "NUMBER"},
            "reasoning": {"type": "STRING"},
        },
        "required": ["vehicle", "confidence", "reasoning"],
    },
}
COMMENT_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "spam": {"type": "BOOLEAN"},
            "polarity": {"type": "STRING", "enum": ["pos", "neu", "neg"]},
            "theme": {"type": "STRING", "enum": config.THEMES},
            "language": {"type": "STRING", "enum": ["en", "hi", "hinglish", "other"]},
        },
        "required": ["spam", "polarity", "theme", "language"],
    },
}


def gemini_json(prompt: str, schema: dict, api_key: str) -> list:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.1,
        },
    }
    resp = requests.post(GEMINI_API, params={"key": api_key}, json=body, timeout=120)
    if not resp.ok:
        raise RuntimeError(f"Gemini API failed: {resp.status_code} {resp.text[:300]}")
    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"unexpected Gemini response shape: {data}") from exc
    import json
    return json.loads(text)


# ═══════════════════════════════ POSTS ═══════════════════════════════

def needs_classification(rec: dict) -> bool:
    return rec.get("model_version") != CURRENT_MODEL_VERSION


def classify_posts_batch(batch: list[dict], api_key: str) -> list[dict]:
    lines = []
    for i, rec in enumerate(batch):
        caption = (rec.get("caption") or "").replace("\n", " ")[:600]
        lines.append(f"{i}. post_type={rec.get('post_type')} caption=\"{caption}\"")
    prompt = (
        "You are classifying Indian beer-brand social posts by SURROGATE ADVERTISING vehicle "
        "(Indian law bars direct alcohol ads, so brands market through these vehicles instead). "
        "For each numbered post below, return one JSON object with:\n"
        "- vehicle: one of soda, nonalc, music, merch, direct, unclassified\n"
        "  soda = packaged water/soda surrogate products; nonalc = 0.0/non-alcoholic variant; "
        "music = festivals/gigs/sponsorships; merch = apparel/glassware/lifestyle merch; "
        "direct = product-forward content that doesn't fit the above; "
        "unclassified = you are genuinely unsure\n"
        "- confidence: 0.0-1.0, your genuine confidence, not padded\n"
        "- reasoning: one short clause\n\n"
        "Return a JSON array with exactly one result per post, in the same order, no other text.\n\n"
        + "\n".join(lines)
    )
    results = gemini_json(prompt, VEHICLE_SCHEMA, api_key)
    if len(results) != len(batch):
        raise RuntimeError(f"Gemini returned {len(results)} results for a batch of {len(batch)}")
    return results


def classify_posts(api_key: str | None = None) -> str:
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    started_at = store.now_iso()
    if not api_key:
        store.append_pull_log("classify_posts", started_at, store.now_iso(), 0, 0, "error", "GEMINI_API_KEY not set")
        return "error"

    posts = store.load_posts()
    pending: list[dict] = []
    for brand_id, records in posts.items():
        for rec in records:
            if needs_classification(rec):
                pending.append(rec)

    total_in = len(pending)
    total_done = 0
    errors: list[str] = []
    for i in range(0, len(pending), POST_BATCH_SIZE):
        batch = pending[i:i + POST_BATCH_SIZE]
        try:
            results = classify_posts_batch(batch, api_key)
            for rec, res in zip(batch, results):
                confidence = float(res.get("confidence", 0))
                vehicle = res.get("vehicle") if confidence >= config.VEHICLE_CONFIDENCE_FLOOR else "unclassified"
                rec["vehicle"] = vehicle
                rec["confidence"] = confidence
                rec["model_version"] = CURRENT_MODEL_VERSION
                rec["classified_at"] = store.now_iso()
                total_done += 1
        except Exception as exc:  # noqa: BLE001 — one bad batch must not sink the run
            errors.append(str(exc))
            print(f"[classify_posts] ERROR on batch {i}: {exc}", file=sys.stderr)

    store.save_posts(posts)
    finished_at = store.now_iso()
    if errors and total_done == 0:
        status = "error"
    elif errors or (total_in and not total_done):
        status = "warn"
    elif total_in == 0:
        status = "ok"  # nothing pending is a legitimate steady state, not a failure
    else:
        status = "ok"
    store.append_pull_log("classify_posts", started_at, finished_at, total_in, total_done, status,
                           "; ".join(errors) if errors else None)
    print(f"[classify_posts] done: status={status} pending={total_in} classified={total_done}")
    return status


# ═══════════════════════════════ COMMENTS ═══════════════════════════════

def select_top_posts(posts: dict, brand_id: str, platform: str, n: int) -> list[dict]:
    records = [r for r in posts.get(brand_id, []) if r.get("platform") == platform]
    scored = sorted(records, key=lambda r: (r.get("likes") or 0) + (r.get("comments") or 0), reverse=True)
    return scored[:n]


def fetch_youtube_comments(video_id: str, api_key: str, max_n: int = config.YT_COMMENT_PER_POST) -> list[dict]:
    out: list[dict] = []
    page_token = None
    while len(out) < max_n:
        params = {
            "part": "snippet", "videoId": video_id, "maxResults": min(100, max_n - len(out)),
            "textFormat": "plainText", "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params, timeout=30)
        if not resp.ok:
            if resp.status_code == 403:
                break  # comments disabled on this video — not an error, just nothing to fetch
            raise RuntimeError(f"YouTube commentThreads failed: {resp.status_code} {resp.text[:200]}")
        data = resp.json()
        for item in data.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            out.append({
                "external_id": item["id"],
                "text": top.get("textDisplay", ""),
                "posted_at": top.get("publishedAt"),
                "likes": top.get("likeCount"),
            })
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return out[:max_n]


def fetch_instagram_comments(post_url: str, apify_token: str, max_n: int = config.IG_COMMENT_PER_POST,
                              actor: str = "apify~instagram-comment-scraper") -> list[dict]:
    run_input = {"directUrls": [post_url], "resultsLimit": max_n}
    resp = requests.post(
        f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items",
        params={"token": apify_token}, json=run_input, timeout=180,
    )
    if not resp.ok:
        raise RuntimeError(f"Apify comment actor failed: {resp.status_code} {resp.text[:200]}")
    items = resp.json()
    usage.record_usage("classify_comments_ig", len(items))
    out = []
    for item in items[:max_n]:
        out.append({
            "external_id": str(item.get("id") or item.get("commentId") or f"{post_url}:{len(out)}"),
            "text": item.get("text") or "",
            "posted_at": item.get("timestamp"),
            "likes": item.get("likesCount"),
        })
    return out


def classify_comments_batch(batch: list[dict], api_key: str) -> list[dict]:
    lines = []
    for i, c in enumerate(batch):
        text = (c.get("text") or "").replace("\n", " ")[:400]
        lines.append(f'{i}. "{text}"')
    prompt = (
        "You are moderating and tagging comments on Indian beer-brand social posts. Comments are "
        "heavily Hinglish and code-mixed (Hindi written in Latin script, mixed with English) — read "
        "them as a native speaker of that mix would, not as English-only text.\n\n"
        "For each numbered comment, return one JSON object with:\n"
        "- spam: true for tag-a-friend bait, giveaway farming, bot/copy-paste replies, unrelated promo\n"
        "- polarity: pos, neu, or neg toward the brand/product (ignore this field's accuracy if spam=true)\n"
        "- theme: one of availability, price, taste, events, nostalgia, other — the comment's main topic\n"
        "- language: en, hi, hinglish, or other\n\n"
        "Return a JSON array with exactly one result per comment, in the same order, no other text.\n\n"
        + "\n".join(lines)
    )
    results = gemini_json(prompt, COMMENT_SCHEMA, api_key)
    if len(results) != len(batch):
        raise RuntimeError(f"Gemini returned {len(results)} results for a batch of {len(batch)}")
    return results


def classify_comments(youtube_key: str | None = None, apify_token: str | None = None,
                       gemini_key: str | None = None) -> str:
    """Priority rule (RULE 7): post ingestion always wins, comment fetching is
    what gets cut. YouTube comments are free within quota and sampled
    generously (config.YT_COMMENT_POSTS/PER_POST); Instagram comments cost
    Apify credit shared with pull_instagram.py's post scraping, sampled much
    thinner (config.IG_COMMENT_POSTS/PER_POST) and gated on the monthly
    spend ceiling — once over budget, Instagram comment fetching is skipped
    (logged as `warn`, never fails the run) and YouTube comments continue."""
    youtube_key = youtube_key or os.environ.get("YOUTUBE_API_KEY")
    apify_token = apify_token or os.environ.get("APIFY_TOKEN")
    gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY")
    started_at = store.now_iso()
    if not gemini_key:
        store.append_pull_log("classify_comments", started_at, store.now_iso(), 0, 0, "error", "GEMINI_API_KEY not set")
        return "error"

    posts = store.load_posts()
    comments = store.load_comments()
    total_fetched = 0
    total_classified = 0
    errors: list[str] = []
    ig_skipped_over_ceiling = False

    for brand_id in config.BRANDS:
        bucket = comments.setdefault(brand_id, [])
        by_key = {c["external_id"]: c for c in bucket}

        sample_posts: list[tuple[dict, str]] = []
        if youtube_key:
            sample_posts += [(p, "yt") for p in select_top_posts(posts, brand_id, "yt", config.YT_COMMENT_POSTS)]
        if apify_token:
            sample_posts += [(p, "ig") for p in select_top_posts(posts, brand_id, "ig", config.IG_COMMENT_POSTS)]

        for post, platform in sample_posts:
            try:
                if platform == "yt":
                    fetched = fetch_youtube_comments(post["external_id"], youtube_key)
                else:
                    if usage.over_ceiling():
                        ig_skipped_over_ceiling = True
                        continue
                    fetched = fetch_instagram_comments(post.get("media_url", ""), apify_token)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{brand_id}/{post['key']}: fetch failed: {exc}")
                print(f"[classify_comments] ERROR fetching {post['key']}: {exc}", file=sys.stderr)
                continue

            for c in fetched:
                if c["external_id"] in by_key:
                    continue  # already have this one
                c["posted_at"] = c.get("posted_at") or post.get("posted_at")
                c["platform"] = platform  # so build_data.py can report meta.commentSample's yt/ig split
                c.setdefault("spam", None)
                c.setdefault("polarity", None)
                c.setdefault("theme", None)
                c.setdefault("language", None)
                c.setdefault("model_version", None)
                bucket.append(c)
                by_key[c["external_id"]] = c
                total_fetched += 1

        pending = [c for c in bucket if needs_classification(c)]
        for i in range(0, len(pending), POST_BATCH_SIZE):
            batch = pending[i:i + POST_BATCH_SIZE]
            try:
                results = classify_comments_batch(batch, gemini_key)
                for c, res in zip(batch, results):
                    c["spam"] = bool(res.get("spam"))
                    c["polarity"] = res.get("polarity")
                    c["theme"] = res.get("theme")
                    c["language"] = res.get("language")
                    c["model_version"] = CURRENT_MODEL_VERSION
                    c["classified_at"] = store.now_iso()
                    total_classified += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{brand_id} comment batch: {exc}")
                print(f"[classify_comments] ERROR classifying batch for {brand_id}: {exc}", file=sys.stderr)

    store.save_comments(comments)
    finished_at = store.now_iso()
    if ig_skipped_over_ceiling:
        note = f"Instagram comment fetching skipped — over ${config.APIFY_MONTHLY_CEILING_USD:.2f}/mo ceiling"
        errors.append(note)
        print(f"[classify_comments] WARN {note}")
    if errors and total_classified == 0 and not ig_skipped_over_ceiling:
        status = "error"
    elif errors:
        status = "warn"
    else:
        status = "ok"
    store.append_pull_log("classify_comments", started_at, finished_at, total_fetched, total_classified, status,
                           "; ".join(errors) if errors else None)
    print(f"[classify_comments] done: status={status} fetched={total_fetched} classified={total_classified} "
          f"apify_month_to_date=${usage.month_to_date_usd():.2f}")
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--posts-only", action="store_true")
    parser.add_argument("--comments-only", action="store_true")
    args = parser.parse_args()

    statuses = []
    if not args.comments_only:
        statuses.append(classify_posts())
    if not args.posts_only:
        statuses.append(classify_comments())
    sys.exit(0 if all(s == "ok" for s in statuses) else 1)


if __name__ == "__main__":
    main()
