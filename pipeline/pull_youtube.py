"""
pull_youtube.py — Phase 2.

Free within quota (10,000 units/day), so this runs first and needs no paid
credit. Per brand with a YouTube presence:

  1. channels.list  part=statistics                         -> subscribers, video count
  2. search.list    part=snippet&order=date&publishedAfter=  -> recent video IDs (last 90d)
  3. videos.list     part=statistics,contentDetails            -> views, likes, comments, duration

Upserts into store/posts.json (dedupe key "yt:<video_id>" — see store.py).
Logs one pull_log row for the whole run. A run that writes zero rows across
every brand is a `warn`, not an `ok` — see RULES #6 in the build prompt.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

from . import config, store

YT_API = "https://www.googleapis.com/youtube/v3"
ISO8601_DURATION_RE = re.compile(
    r"P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def parse_iso8601_duration(s: str) -> int:
    """'PT1H2M10S' -> 3730. YouTube durations are always in this form."""
    m = ISO8601_DURATION_RE.match(s or "")
    if not m:
        return 0
    parts = m.groupdict()
    days = int(parts["days"] or 0)
    hours = int(parts["hours"] or 0)
    minutes = int(parts["minutes"] or 0)
    seconds = int(parts["seconds"] or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _get(path: str, api_key: str, **params) -> dict:
    params = {**params, "key": api_key}
    resp = requests.get(f"{YT_API}/{path}", params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"YouTube API {path} failed: {resp.status_code} {resp.text[:300]}")
    return resp.json()


def resolve_channel_id(handle: str, api_key: str) -> str | None:
    """Resolve a stable channel ID from an @handle. Prefer pinning
    `yt_channel_id` in config.py once known — a handle can be renamed
    without the ID changing, so re-resolving every run buys nothing and
    costs a quota unit for no reason."""
    data = _get("channels", api_key, part="id", forHandle=handle.lstrip("@"))
    items = data.get("items") or []
    return items[0]["id"] if items else None


def get_channel_stats(channel_id: str, api_key: str) -> dict:
    data = _get("channels", api_key, part="statistics", id=channel_id)
    items = data.get("items") or []
    if not items:
        return {"subscribers": None, "video_count": None}
    stats = items[0]["statistics"]
    return {
        "subscribers": int(stats["subscriberCount"]) if "subscriberCount" in stats and not stats.get("hiddenSubscriberCount") else None,
        "video_count": int(stats.get("videoCount", 0)),
    }


def search_recent_video_ids(channel_id: str, published_after: str, api_key: str) -> list[str]:
    ids: list[str] = []
    page_token = None
    while True:
        data = _get(
            "search", api_key,
            part="snippet", channelId=channel_id, order="date",
            publishedAfter=published_after, type="video", maxResults=50,
            pageToken=page_token,
        )
        ids.extend(item["id"]["videoId"] for item in data.get("items", []) if item.get("id", {}).get("videoId"))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return ids


def get_videos_details(video_ids: list[str], api_key: str) -> list[dict]:
    out: list[dict] = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        data = _get("videos", api_key, part="statistics,contentDetails,snippet", id=",".join(chunk))
        out.extend(data.get("items", []))
    return out


def build_post_record(video: dict) -> dict:
    stats = video.get("statistics", {})
    snippet = video.get("snippet", {})
    content = video.get("contentDetails", {})
    return {
        "external_id": video["id"],
        "posted_at": snippet.get("publishedAt"),
        "post_type": "video",
        "caption": snippet.get("title", "") + ("\n\n" + snippet.get("description", "") if snippet.get("description") else ""),
        "media_url": f"https://www.youtube.com/watch?v={video['id']}",
        "views": int(stats["viewCount"]) if "viewCount" in stats else None,
        "likes": int(stats["likeCount"]) if "likeCount" in stats else None,
        "comments": int(stats["commentCount"]) if "commentCount" in stats else None,
        "duration_s": parse_iso8601_duration(content.get("duration", "")),
    }


def run(api_key: str | None = None) -> tuple[str, dict]:
    api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
    started_at = store.now_iso()
    if not api_key:
        finished_at = store.now_iso()
        store.append_pull_log("pull_youtube", started_at, finished_at, 0, 0, "error", "YOUTUBE_API_KEY not set")
        return "error", {}

    posts = store.load_posts()
    channel_stats = store.load_channel_stats()
    published_after = (datetime.now(timezone.utc) - timedelta(days=config.YOUTUBE_LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")

    total_in = 0
    total_upserted = 0
    per_brand = {}
    errors = []

    for brand_id, brand in config.BRANDS.items():
        channel_id = brand.get("yt_channel_id")
        handle = brand.get("yt_handle")
        if not channel_id and not handle:
            continue
        try:
            if not channel_id:
                channel_id = resolve_channel_id(handle, api_key)
                if not channel_id:
                    raise RuntimeError(f"could not resolve channel for handle {handle}")

            stats = get_channel_stats(channel_id, api_key)
            channel_stats.setdefault(brand_id, {})["yt"] = {
                "followers": stats["subscribers"],
                "video_count": stats["video_count"],
                "channel_id": channel_id,
                "updated_at": store.now_iso(),
            }

            video_ids = search_recent_video_ids(channel_id, published_after, api_key)
            videos = get_videos_details(video_ids, api_key) if video_ids else []
            records = [build_post_record(v) for v in videos]

            rows_in, rows_new, rows_updated = store.upsert_posts(posts, brand_id, "yt", records)
            total_in += rows_in
            total_upserted += rows_new + rows_updated
            per_brand[brand_id] = {"videos_seen": rows_in, "new": rows_new, "updated": rows_updated,
                                    "subscribers": stats["subscribers"]}
            print(f"[pull_youtube] {brand_id}: {rows_in} videos seen, {rows_new} new, {rows_updated} refreshed, "
                  f"{stats['subscribers']} subscribers")
        except Exception as exc:  # noqa: BLE001 — one brand's failure must not sink the whole run
            errors.append(f"{brand_id}: {exc}")
            print(f"[pull_youtube] ERROR {brand_id}: {exc}", file=sys.stderr)

    store.save_posts(posts)
    store.save_channel_stats(channel_stats)

    finished_at = store.now_iso()
    if errors and not per_brand:
        status = "error"
    elif total_upserted == 0:
        status = "warn"
    elif errors:
        status = "warn"
    else:
        status = "ok"

    error_text = "; ".join(errors) if errors else None
    store.append_pull_log("pull_youtube", started_at, finished_at, total_in, total_upserted, status, error_text)
    print(f"[pull_youtube] done: status={status} rows_in={total_in} rows_upserted={total_upserted}")
    return status, per_brand


def main() -> None:
    status, _ = run()
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
