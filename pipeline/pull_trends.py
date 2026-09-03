"""
pull_trends.py — Phase 6.

Weekly, not daily — the unofficial Trends API rate-limits aggressively and
the series barely moves day to day, so a daily pull would just burn through
rate limit for no signal.

Google Trends returns values 0-100 *relative to the other terms in the same
request*, and caps a request at 5 terms — 8 brands don't fit in one call.
So every batch carries a shared anchor brand (the client, Kingfisher) plus
up to 4 others; the anchor's series from the first batch becomes the
reference scale, and every later batch is rescaled by
(reference anchor mean / this batch's anchor mean) before its brands are
recorded. Without the anchor, batch 2's "100" and batch 1's "100" mean
different things and the eight series aren't comparable at all.

Each brand's exact query string lives in config.py (`trends_query`) and is
surfaced verbatim in meta.trendsQueries — "Kingfisher" vs "Kingfisher beer"
return genuinely different series (the bare name is contaminated by the
airline and the bird), so the query actually used has to be visible.
"""

from __future__ import annotations

import sys
import time

from . import config, store

BATCH_SIZE = 5           # Google Trends' hard cap per request
TIMEFRAME = "today 3-m"  # ~90 days, then bucketed into 6 points downstream
SERIES_BUCKETS = 6
REQUEST_DELAY_S = 2      # polite pacing against an unofficial, rate-limited API


def make_batches(anchor_id: str, brand_ids: list[str]) -> list[list[str]]:
    """Split brand_ids into groups of <=5 that each include the anchor, so
    every batch can be rescaled back onto the anchor's reference value."""
    others = [b for b in brand_ids if b != anchor_id]
    chunk = BATCH_SIZE - 1
    batches = [[anchor_id] + others[i:i + chunk] for i in range(0, len(others), chunk)]
    return batches or [[anchor_id]]


def bucket_series(df, kw: str, buckets: int = SERIES_BUCKETS) -> list[float]:
    """Collapse a daily interest_over_time column into `buckets` evenly
    spaced means — the same 6-point convention as seriesIG/seriesYT."""
    if df is None or df.empty or kw not in df.columns:
        return [0.0] * buckets
    values = df[kw].tolist()
    n = len(values)
    if n == 0:
        return [0.0] * buckets
    out = []
    for i in range(buckets):
        lo = int(i * n / buckets)
        hi = max(lo + 1, int((i + 1) * n / buckets))
        chunk = values[lo:hi]
        out.append(round(sum(chunk) / len(chunk), 1) if chunk else 0.0)
    return out


def fetch_batch(pytrends, queries: dict, batch_ids: list[str]):
    kw_list = [queries[b] for b in batch_ids]
    pytrends.build_payload(kw_list, timeframe=TIMEFRAME, geo="IN")
    return pytrends.interest_over_time()


def run(pytrends_factory=None) -> str:
    started_at = store.now_iso()
    try:
        if pytrends_factory is None:
            from pytrends.request import TrendReq
            pytrends_factory = lambda: TrendReq(hl="en-US", tz=330)  # noqa: E731
        pytrends = pytrends_factory()
    except Exception as exc:  # noqa: BLE001
        store.append_pull_log("pull_trends", started_at, store.now_iso(), 0, 0, "error", str(exc))
        print(f"[pull_trends] could not initialise pytrends: {exc}", file=sys.stderr)
        return "error"

    anchor_id = config.client_brand_id()
    brand_ids = list(config.BRANDS.keys())
    queries = {bid: b["trends_query"] for bid, b in config.BRANDS.items()}
    batches = make_batches(anchor_id, brand_ids)

    results: dict[str, list[float]] = {}
    anchor_reference: list[float] | None = None
    errors: list[str] = []

    for batch_ids in batches:
        try:
            df = fetch_batch(pytrends, queries, batch_ids)
            anchor_series = bucket_series(df, queries[anchor_id])
            if anchor_reference is None:
                anchor_reference = anchor_series
                scale = 1.0
            else:
                ref_mean = (sum(anchor_reference) / len(anchor_reference)) or 1.0
                this_mean = (sum(anchor_series) / len(anchor_series)) or 1.0
                scale = ref_mean / this_mean
            for bid in batch_ids:
                if bid in results:
                    continue
                series = bucket_series(df, queries[bid])
                results[bid] = [round(v * scale, 1) for v in series]
        except Exception as exc:  # noqa: BLE001 — one bad batch must not sink the run
            errors.append(f"batch {batch_ids}: {exc}")
            print(f"[pull_trends] ERROR batch {batch_ids}: {exc}", file=sys.stderr)
        time.sleep(REQUEST_DELAY_S)

    trends_out = {
        bid: {"series": results.get(bid, [0] * SERIES_BUCKETS), "query": queries[bid], "fetched_at": store.now_iso()}
        for bid in brand_ids
    }
    store.save_json(config.TRENDS_PATH, trends_out)

    finished_at = store.now_iso()
    rows_ok = sum(1 for bid in brand_ids if bid in results)
    if errors and rows_ok == 0:
        status = "error"
    elif errors or rows_ok == 0:
        status = "warn"
    else:
        status = "ok"
    store.append_pull_log("pull_trends", started_at, finished_at, len(brand_ids), rows_ok, status,
                           "; ".join(errors) if errors else None)
    print(f"[pull_trends] done: status={status} brands={rows_ok}/{len(brand_ids)}")
    return status


def main() -> None:
    status = run()
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
