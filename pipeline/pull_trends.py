"""
pull_trends.py — Phase 6.

Weekly, not daily — the unofficial Trends API rate-limits aggressively and
the series barely moves day to day, so a daily pull would just burn through
rate limit for no signal.

Google Trends returns values 0-100 *relative to the other terms in the same
request*, and caps a request at 5 terms — a tracked set bigger than that
doesn't fit in one call. So every batch carries a shared anchor brand
(config.TRENDS_ANCHOR — the client, by convention) plus up to 4 others;
the anchor's series from the first batch becomes the reference scale, and
every later batch is rescaled by (reference anchor mean / this batch's
anchor mean) before its brands are recorded. Without the anchor, batch 2's
"100" and batch 1's "100" mean different things and the tracked set's
series aren't comparable at all.

Each brand's exact query string lives in config.py (`trends_query`) and is
surfaced verbatim in meta.trendsQueries — a bare brand name can be
contaminated by an unrelated same-name thing (config.py's own comments
note this per brand where it applies), so the query actually used has to
be visible rather than assumed from the brand name alone.
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


def bucket_series(df, kw: str, buckets: int = SERIES_BUCKETS) -> list[float | None]:
    """Collapse a daily interest_over_time column into `buckets` evenly
    spaced means — the same 6-point convention as seriesIG/seriesYT.

    A bucket that averages to exactly 0 is Trends reporting "below my
    threshold", not "measured zero interest" (Phase 4 / RULE 3) — when
    config.TRENDS_ZERO_IS_NULL, that bucket comes back as `None` rather than
    0.0, so the front end can draw a gap instead of a line to the floor."""
    if df is None or df.empty or kw not in df.columns:
        return [None if config.TRENDS_ZERO_IS_NULL else 0.0] * buckets
    values = df[kw].tolist()
    n = len(values)
    if n == 0:
        return [None if config.TRENDS_ZERO_IS_NULL else 0.0] * buckets
    out = []
    for i in range(buckets):
        lo = int(i * n / buckets)
        hi = max(lo + 1, int((i + 1) * n / buckets))
        chunk = values[lo:hi]
        mean = round(sum(chunk) / len(chunk), 1) if chunk else 0.0
        if mean == 0.0 and config.TRENDS_ZERO_IS_NULL:
            out.append(None)
        else:
            out.append(mean)
    return out


def fetch_batch(pytrends, queries: dict, batch_ids: list[str]):
    kw_list = [queries[b] for b in batch_ids]
    # geo is never omitted — an ungeo'd query blends in every market Trends
    # covers and the resulting series means nothing for an India read (Phase 5).
    pytrends.build_payload(kw_list, timeframe=TIMEFRAME, geo=config.TRENDS_GEO)
    return pytrends.interest_over_time()


def _mean_ignoring_none(values: list[float | None]) -> float:
    known = [v for v in values if v is not None]
    return (sum(known) / len(known)) if known else 0.0


def run(pytrends_factory=None) -> str:
    started_at = store.now_iso()
    try:
        if pytrends_factory is None:
            from pytrends.request import TrendReq
            pytrends_factory = lambda: TrendReq(hl="en-US", tz=config.TRENDS_TIMEZONE)  # noqa: E731
        pytrends = pytrends_factory()
    except Exception as exc:  # noqa: BLE001
        store.append_pull_log("pull_trends", started_at, store.now_iso(), 0, 0, "error", str(exc))
        print(f"[pull_trends] could not initialise pytrends: {exc}", file=sys.stderr)
        return "error"

    anchor_id = config.TRENDS_ANCHOR
    brand_ids = list(config.BRANDS.keys())
    queries = {bid: b["trends_query"] for bid, b in config.BRANDS.items()}
    batches = make_batches(anchor_id, brand_ids)

    results: dict[str, list[float | None]] = {}
    anchor_reference: list[float | None] | None = None
    errors: list[str] = []

    for batch_ids in batches:
        try:
            df = fetch_batch(pytrends, queries, batch_ids)
            anchor_series = bucket_series(df, queries[anchor_id])
            if anchor_reference is None:
                anchor_reference = anchor_series
                scale = 1.0
            else:
                # Rescaling compounds error on top of Trends' own relative
                # scaling (Phase 5) — this is already the lowest-confidence
                # figure in the product; ignoring null buckets when finding
                # the anchor's mean keeps a below-threshold period from
                # dragging the scale factor toward zero for no reason.
                ref_mean = _mean_ignoring_none(anchor_reference) or 1.0
                this_mean = _mean_ignoring_none(anchor_series) or 1.0
                scale = ref_mean / this_mean
            for bid in batch_ids:
                if bid in results:
                    continue
                series = bucket_series(df, queries[bid])
                results[bid] = [round(v * scale, 1) if v is not None else None for v in series]
        except Exception as exc:  # noqa: BLE001 — one bad batch must not sink the run
            errors.append(f"batch {batch_ids}: {exc}")
            print(f"[pull_trends] ERROR batch {batch_ids}: {exc}", file=sys.stderr)
        time.sleep(REQUEST_DELAY_S)

    trends_out = {
        # A brand missing from `results` entirely (its batch errored) is
        # no more "measured zero" than a below-threshold bucket is — None
        # throughout, same as bucket_series would emit, not a flat 0 line.
        bid: {"series": results.get(bid, [None] * SERIES_BUCKETS), "query": queries[bid], "fetched_at": store.now_iso()}
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
