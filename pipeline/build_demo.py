"""
build_demo.py — Phase 4f.

Reads public/ci/index.html (the live build — fetches ./data.json) and
public/ci/data.json (whatever the aggregator most recently wrote), and
produces dashboard-demo.html: the same file with the fetched data already
loaded, so it opens straight from file:// with no network round-trip.

This doesn't touch a single render function or duplicate any dashboard
logic — it injects one small script block ahead of the main one that sets
`window.__CI_INLINE_DATA__`, and init() (see Phase 4e-ii) already checks for
that before deciding whether to fetch at all. Regenerate whenever you want a
fresh offline snapshot; it's a pure function of the two input files.
"""

from __future__ import annotations

import json
import re
import sys

from . import config

INLINE_MARKER = "<!-- CI_INLINE_DATA -->"


def build_demo_html() -> str:
    if not config.DASHBOARD_LIVE_PATH.exists():
        raise FileNotFoundError(f"{config.DASHBOARD_LIVE_PATH} not found — run this after Phase 4e wiring exists")
    if not config.DATA_JSON_PATH.exists():
        raise FileNotFoundError(f"{config.DATA_JSON_PATH} not found — run build_data.py first")

    html = config.DASHBOARD_LIVE_PATH.read_text(encoding="utf-8")
    data = json.loads(config.DATA_JSON_PATH.read_text(encoding="utf-8"))

    inline_script = (
        f"{INLINE_MARKER}\n"
        f"<script>window.__CI_INLINE_DATA__ = {json.dumps(data, ensure_ascii=False)};</script>\n"
    )

    # Drop any previously injected inline-data block (idempotent regeneration),
    # then insert the fresh one immediately before the main <script> tag.
    html = re.sub(
        re.escape(INLINE_MARKER) + r"\n<script>window\.__CI_INLINE_DATA__ = .*?</script>\n",
        "",
        html,
        flags=re.S,
    )
    marker = "<script>\n'use strict';"
    if marker not in html:
        raise RuntimeError("could not find the main <script> tag to inject inline data before")
    html = html.replace(marker, inline_script + marker, 1)
    return html


def main() -> None:
    try:
        html = build_demo_html()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"[build_demo] {exc}", file=sys.stderr)
        sys.exit(1)
    config.DASHBOARD_DEMO_PATH.write_text(html, encoding="utf-8")
    print(f"[build_demo] wrote {config.DASHBOARD_DEMO_PATH} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
