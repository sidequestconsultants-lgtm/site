"""
preflight.py — Phase 1.

Validates the three API keys a real run needs (YOUTUBE_API_KEY, APIFY_TOKEN,
GEMINI_API_KEY) — present AND reachable — before any pull spends quota or
credit. Every check below is chosen to be free or near-free and to make no
store write: a bad key should fail loudly here, not three minutes into a
`daily.yml` run after `pull_youtube.py` has already written rows.

Exits non-zero if any key is missing or a call with it fails, so this is
meant to run as the first step of the real-run workflow, gating everything
after it.
"""

from __future__ import annotations

import os
import sys

import requests

YOUTUBE_CHECK_URL = "https://www.googleapis.com/youtube/v3/channels"
# Google Developers' own channel — a fixed, always-public ID. part=id only,
# so this costs the minimum possible quota (1 unit) regardless of the key's
# real target brands.
YOUTUBE_CHECK_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"

APIFY_CHECK_URL = "https://api.apify.com/v2/users/me"

GEMINI_CHECK_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def check_youtube(api_key: str | None) -> tuple[bool, str]:
    if not api_key:
        return False, "YOUTUBE_API_KEY not set"
    try:
        resp = requests.get(
            YOUTUBE_CHECK_URL,
            params={"part": "id", "id": YOUTUBE_CHECK_CHANNEL_ID, "key": api_key},
            timeout=15,
        )
        if resp.ok:
            return True, "reachable"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as exc:
        return False, f"request failed: {exc}"


def check_apify(token: str | None) -> tuple[bool, str]:
    if not token:
        return False, "APIFY_TOKEN not set"
    try:
        resp = requests.get(APIFY_CHECK_URL, params={"token": token}, timeout=15)
        if resp.ok:
            return True, "reachable"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as exc:
        return False, f"request failed: {exc}"


def check_gemini(api_key: str | None) -> tuple[bool, str]:
    if not api_key:
        return False, "GEMINI_API_KEY not set"
    try:
        resp = requests.get(GEMINI_CHECK_URL, params={"key": api_key}, timeout=15)
        if resp.ok:
            return True, "reachable"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as exc:
        return False, f"request failed: {exc}"


def run() -> bool:
    checks = [
        ("YOUTUBE_API_KEY", check_youtube(os.environ.get("YOUTUBE_API_KEY"))),
        ("APIFY_TOKEN", check_apify(os.environ.get("APIFY_TOKEN"))),
        ("GEMINI_API_KEY", check_gemini(os.environ.get("GEMINI_API_KEY"))),
    ]
    all_ok = True
    for name, (ok, detail) in checks:
        status = "OK" if ok else "FAIL"
        print(f"[preflight] {name}: {status} ({detail})")
        all_ok = all_ok and ok
    print(f"[preflight] {'all keys valid' if all_ok else 'one or more keys failed — real pulls will not run'}")
    return all_ok


def main() -> None:
    sys.exit(0 if run() else 1)


if __name__ == "__main__":
    main()
