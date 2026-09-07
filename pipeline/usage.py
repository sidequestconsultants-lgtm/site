"""
usage.py — Apify spend tracking against the $4.00/month ceiling (Phase 2).

Apify's exact per-run cost depends on actor compute units, not just result
count, and isn't available without a live billing API call. Rather than
under-count and risk actually exhausting the $5 free credit (which would
starve post ingestion — the one thing that must never happen, RULE 7), this
tracks a deliberately conservative *estimate*: $3.00 per 1,000 results
returned, rounded up. That's above typical published per-result pricing for
scraping actors, so the ceiling trips a bit early rather than late. Treat
this file's number as a local safety brake, not a substitute for checking
the real balance in the Apify console.

Every Apify call — post scraping AND comment scraping — records usage here,
since both draw from the same monthly credit pool. Only comment fetching
checks the ceiling before spending, per RULE 7: post ingestion always
proceeds regardless of remaining budget.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import config, store

ESTIMATED_COST_PER_1000_RESULTS_USD = 3.00


def _usage_path():
    return config.REPO_ROOT / config.USAGE_FILE


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def estimate_cost_usd(result_count: int) -> float:
    return round((result_count / 1000) * ESTIMATED_COST_PER_1000_RESULTS_USD, 4)


def load_usage() -> dict:
    return store.load_json(_usage_path(), {})


def record_usage(fn: str, result_count: int) -> float:
    """Append one call's estimated cost to the current month's total.
    Returns the new month-to-date total."""
    usage = load_usage()
    month = _current_month()
    entry = usage.setdefault(month, {"units_usd": 0.0, "calls": []})
    cost = estimate_cost_usd(result_count)
    entry["units_usd"] = round(entry["units_usd"] + cost, 4)
    entry["calls"].append({"fn": fn, "at": store.now_iso(), "results": result_count, "estimated_usd": cost})
    store.save_json(_usage_path(), usage)
    return entry["units_usd"]


def month_to_date_usd() -> float:
    usage = load_usage()
    return usage.get(_current_month(), {}).get("units_usd", 0.0)


def over_ceiling() -> bool:
    return month_to_date_usd() >= config.APIFY_MONTHLY_CEILING_USD


def remaining_budget_usd() -> float:
    return max(0.0, config.APIFY_MONTHLY_CEILING_USD - month_to_date_usd())
