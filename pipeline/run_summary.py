"""
run_summary.py — the "status is reported, not enforced" step (build prompt
RULE 3). No script in this pipeline exits non-zero for an expected failure
(quota, rate limit, a dead handle, zero rows — see pull_youtube.py/
pull_instagram.py/classify.py/pull_trends.py's own main()), so a green
GitHub Actions run tells a human nothing about what actually happened.
This reads the same store/pull_log.json every one of those scripts already
appends to (source of truth already exists — this is a report, not a new
recording mechanism) and prints a markdown summary: what ran, what it
skipped and why, how many rows, and Apify spend against the monthly ceiling
(the one quota this pipeline can see numerically rather than only after
the fact from a 403).

Run standalone (`python -m pipeline.run_summary`) for the
`$GITHUB_STEP_SUMMARY` workflow step. `latest_entries()` and
`describe_entry()` are also imported by build_data.py to build
meta.sources — the dashboard's own version of this same status, so a
viewer sees the same "what's degraded and why" a human reading the
Actions summary would.
"""

from __future__ import annotations

from . import config, store, usage

# Every fn name any pull/classify script appends to pull_log.json under,
# in the order a human reading top-to-bottom would want them.
KNOWN_FNS = ["pull_youtube", "pull_instagram", "classify_posts", "classify_comments", "pull_trends"]


def latest_entries(pull_log: list[dict]) -> dict[str, dict]:
    """The most recent pull_log.json row for each fn — every script's
    status logic already folds a whole run's worth of per-brand detail
    into one row, so the last one IS that script's current state."""
    latest: dict[str, dict] = {}
    for entry in pull_log:
        latest[entry["fn"]] = entry
    return latest


def describe_entry(entry: dict | None) -> str:
    if entry is None:
        return "never run"
    parts = [f"`{entry['status']}`", f"{entry.get('rows_upserted', 0)}/{entry.get('rows_in', 0)} rows"]
    if entry.get("error"):
        parts.append(entry["error"][:200])
    return " — ".join(parts)


def build_summary_lines() -> list[str]:
    pull_log = store.load_json(config.PULL_LOG_PATH, [])
    latest = latest_entries(pull_log)

    lines = ["### Pipeline run summary", ""]
    for fn in KNOWN_FNS:
        lines.append(f"- **{fn}**: {describe_entry(latest.get(fn))}")

    known = set(KNOWN_FNS)
    extra = sorted(set(latest) - known)
    for fn in extra:
        lines.append(f"- **{fn}**: {describe_entry(latest[fn])}")

    spend = usage.month_to_date_usd()
    lines += [
        "",
        f"Apify spend this month: **${spend:.2f}** / ${config.APIFY_MONTHLY_CEILING_USD:.2f} ceiling"
        + (" — **OVER CEILING**, Instagram comment fetching skips until next month" if spend >= config.APIFY_MONTHLY_CEILING_USD else ""),
        "",
        "Full per-run detail (row counts, per-brand status, every quota/error message) is in `store/pull_log.json`, committed above.",
    ]
    return lines


def main() -> None:
    print("\n".join(build_summary_lines()))


if __name__ == "__main__":
    main()
