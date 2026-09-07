"""
Shared JSON store I/O for the pipeline. No database — dedupe-by-key against
flat files IS the idempotency guarantee (see build prompt Phase 1). Every
write goes through an atomic write-then-rename so a crashed run never leaves
a half-written store file behind.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            return default
        return json.loads(text)


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=False)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_posts() -> dict:
    return load_json(config.POSTS_PATH, {})


def save_posts(posts: dict) -> None:
    save_json(config.POSTS_PATH, posts)


def load_comments() -> dict:
    return load_json(config.COMMENTS_PATH, {})


def save_comments(comments: dict) -> None:
    save_json(config.COMMENTS_PATH, comments)


def load_channel_stats() -> dict:
    return load_json(config.STORE_DIR / "channel_stats.json", {})


def save_channel_stats(stats: dict) -> None:
    save_json(config.STORE_DIR / "channel_stats.json", stats)


def upsert_posts(posts: dict, brand_id: str, platform: str, records: list[dict]) -> tuple[int, int, int]:
    """
    Merge `records` (each must carry an `external_id`) into posts[brand_id],
    deduping on `key = "<platform>:<external_id>"`. An existing key is
    UPDATED in place (view/like/comment counts refreshed, first_seen kept,
    last_fetched bumped) rather than appended again — this is the whole of
    idempotency here; skip it and every re-run inflates every metric.

    Returns (rows_in, rows_new, rows_updated).
    """
    bucket = posts.setdefault(brand_id, [])
    by_key = {r["key"]: r for r in bucket}
    new_count = 0
    updated_count = 0
    now = now_iso()
    for rec in records:
        key = f"{platform}:{rec['external_id']}"
        rec = dict(rec)
        rec["key"] = key
        rec["platform"] = platform
        rec["last_fetched"] = now
        existing = by_key.get(key)
        if existing is None:
            rec.setdefault("first_seen", now)
            rec.setdefault("vehicle", None)
            rec.setdefault("confidence", None)
            rec.setdefault("model_version", None)
            rec.setdefault("paid_est", None)
            rec.setdefault("organic_est", None)
            bucket.append(rec)
            by_key[key] = rec
            new_count += 1
        else:
            # refresh volatile counters only; never clobber classification fields
            for field in ("posted_at", "post_type", "caption", "media_url",
                           "views", "likes", "comments", "duration_s"):
                if field in rec:
                    existing[field] = rec[field]
            existing["last_fetched"] = now
            updated_count += 1
    return (len(records), new_count, updated_count)


def append_pull_log(fn: str, started_at: str, finished_at: str,
                     rows_in: int, rows_upserted: int, status: str, error: str | None = None) -> None:
    log = load_json(config.PULL_LOG_PATH, [])
    log.append({
        "fn": fn,
        "started_at": started_at,
        "finished_at": finished_at,
        "rows_in": rows_in,
        "rows_upserted": rows_upserted,
        "status": status,
        "error": error,
    })
    # keep the log from growing unbounded across years of daily runs
    save_json(config.PULL_LOG_PATH, log[-500:])
