"""
verify_handles.py — Phase 1.

Read-only handle/channel verification report. Makes no store write and
spends no Apify credit — Apify is the only programmatic way to check an
Instagram handle, and burning credit just to print a report would eat into
the same $4/mo ceiling `classify.py` is rationed against, for a check a
human doing the actual verification pass has to eyeball anyway. So:

  - Instagram / Facebook: prints the handle and its constructed profile URL
    for a human to open and confirm against config.py's `verified` flag.
  - YouTube: `channels.list?forHandle=` is free within quota (1 unit/brand),
    so this resolves the real channel and prints its title, subscriber
    count and channel ID straight from the API — the same call
    `pull_youtube.py` makes, just without ever touching the store.

Run this, read the output, and only then flip `verified: True` in
config.py by hand (see pipeline/README.md, "Before the first real run").
"""

from __future__ import annotations

import os
import sys

from . import config
from .pull_youtube import _get, _looks_like_channel_id


def youtube_lookup(handle: str, api_key: str) -> dict:
    if _looks_like_channel_id(handle):
        data = _get("channels", api_key, part="snippet,statistics", id=handle)
    else:
        data = _get("channels", api_key, part="snippet,statistics", forHandle=handle.lstrip("@"))
    items = data.get("items") or []
    if not items:
        return {"resolved": False}
    item = items[0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})
    return {
        "resolved": True,
        "channel_id": item["id"],
        "title": snippet.get("title"),
        "subscribers": None if stats.get("hiddenSubscriberCount") else stats.get("subscriberCount"),
        "video_count": stats.get("videoCount"),
    }


def run() -> None:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("[verify_handles] YOUTUBE_API_KEY not set — YouTube rows will show manual-check URLs only",
              file=sys.stderr)

    for brand_id, brand in config.BRANDS.items():
        print(f"\n[verify_handles] {brand_id} ({brand['name']}) — config.verified={brand.get('verified')}")

        handles_ig = brand.get("handle_ig") or []
        if handles_ig:
            for handle_ig in handles_ig:
                print(f"  ig  @{handle_ig:<30} https://www.instagram.com/{handle_ig}/  (open and confirm by hand)")
        else:
            print("  ig  (no handle_ig in config)")

        handle_fb = brand.get("handle_fb")
        handles_fb = handle_fb if isinstance(handle_fb, list) else ([handle_fb] if handle_fb else [])
        if handles_fb:
            for fb in handles_fb:
                print(f"  fb  {fb:<31} https://www.facebook.com/{fb}  (open and confirm by hand)")
        else:
            print("  fb  (no handle_fb in config)")

        yt_handle = brand.get("yt_handle")
        if not yt_handle:
            print("  yt  (no yt_handle in config)")
            continue
        if not api_key:
            print(f"  yt  {yt_handle:<31} https://www.youtube.com/{yt_handle}  (open and confirm by hand)")
            continue
        try:
            result = youtube_lookup(yt_handle, api_key)
        except Exception as exc:  # noqa: BLE001 — one brand's failure must not sink the report
            print(f"  yt  {yt_handle}: ERROR {exc}", file=sys.stderr)
            continue
        if not result["resolved"]:
            print(f"  yt  {yt_handle}: NOT RESOLVED — forHandle= found no channel, check the handle by hand")
            continue
        print(f"  yt  {yt_handle:<31} \"{result['title']}\" · {result['subscribers']} subscribers · "
              f"{result['video_count']} videos · channel_id={result['channel_id']}")


def main() -> None:
    run()
    sys.exit(0)


if __name__ == "__main__":
    main()
