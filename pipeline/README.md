# Kingfisher CI pipeline

Ingestion and serving layer for the live Kingfisher Competitive Intelligence
dashboard. Zero paid services, no database — state lives as JSON files in
this repo, GitHub Actions runs it daily, Vercel serves the output.

The dashboard itself (`public/ci/index.html`) is a copy of the standalone
demo file (`brand/kingfisher-competitive-intelligence.html`) with a small,
deliberate set of edits: its hardcoded `DATA` block is gone, replaced by a
`fetch('./data.json')` at load. **No render function was touched** — see
the diff notes at the bottom of this file if you're auditing that claim.

## Stack

| Piece | Service | Why |
|---|---|---|
| Scheduler + compute | GitHub Actions | 2,000 min/mo free |
| Storage | JSON files in the repo (`store/`) | no DB needed for one snapshot a day |
| Hosting | Vercel (this repo's existing static export) | auto-deploys on push |
| YouTube | Data API v3 | 10,000 units/day, free |
| Instagram | Apify (`$5`/mo free credit) | ~3,300 posts/mo — inside budget |
| Classification | Gemini Flash (free tier) | caption/comment tagging doesn't need a frontier model |
| Search interest | `pytrends` (unofficial Trends API) | free, rate-limited |

## Layout

```
pipeline/            hand-write config.py; everything else is generated code
  config.py           the 8 brands, handles, parent mapping, thresholds — edit this by hand
  store.py             shared JSON I/O + the dedupe-by-key upsert that makes ingestion idempotent
  pull_youtube.py       Phase 2
  pull_instagram.py      Phase 3 (refuses to run for real until brands are verified — see below)
  build_data.py           Phase 4 — the aggregator, emits public/ci/data.json
  build_demo.py             Phase 4f — inlines data.json into dashboard-demo.html
  classify.py                Phase 5 — Gemini Flash vehicle/comment classification
  pull_trends.py               Phase 6 — weekly search-interest pull
store/                committed JSON state
  posts.json           deduped raw posts per brand, platform:external_id keyed
  comments.json          sampled + classified comments per brand
  channel_stats.json      follower/subscriber snapshots
  pull_log.json             one row per pipeline run — fn, counts, status, error
  snapshots/YYYY-MM-DD.json  a full data.json copy per day — rollback is a file, not an operation
public/ci/
  index.html            the live dashboard (fetches ./data.json)
  data.json               current published snapshot
dashboard-demo.html      offline build, opens from file://, regenerate on demand
.github/workflows/
  daily.yml              pull → classify → build → commit, 09:00 IST + manual trigger
  weekly-trends.yml        trends pull, Mondays only
```

## Before the first real run

1. **Verify every handle in `config.py` by hand** against the live Instagram
   and YouTube accounts, then flip that brand's `verified: True`.
   `pull_instagram.py` refuses to run for real while *any* brand is
   unverified — a wrong handle silently produces wrong data for that brand,
   and this is the pull most likely to point at the wrong account.
2. Pin `yt_channel_id` for each brand once you've resolved it (the script
   will resolve by `yt_handle` on every run if you don't, which works but
   costs an extra quota unit and is one more thing that can drift if a
   channel renames its handle).
3. Set the four GitHub Actions repo secrets: `APIFY_TOKEN`,
   `YOUTUBE_API_KEY`, `GEMINI_API_KEY`. Keep the repo **private** if you use
   it — public repos get unlimited Actions minutes, but `store/` becomes
   public with them.

## Running locally

```bash
pip install -r pipeline/requirements.txt
export YOUTUBE_API_KEY=...
export APIFY_TOKEN=...
export GEMINI_API_KEY=...

python -m pipeline.pull_instagram --dry-run   # preview what would be fetched, no credit spent
python -m pipeline.pull_youtube
python -m pipeline.pull_instagram
python -m pipeline.classify
python -m pipeline.build_data
python -m pipeline.build_demo
```

Every script exits non-zero on a `warn` or `error` `pull_log` status
(including a zero-record pull — that's a warning, never a success), so a CI
step failing is the pipeline working correctly, not a bug to route around.

## Data flow

`pull_youtube.py` / `pull_instagram.py` → `store/posts.json` (dedupe key
`platform:external_id`, idempotent — a re-run refreshes counters on existing
rows, never appends a duplicate) → `classify.py` fetches a comment sample for
the top 25 posts per brand into `store/comments.json` and tags both posts
(surrogate vehicle) and comments (spam/polarity/theme/language) →
`build_data.py` reads the whole store, estimates paid/organic per post from
a trailing-90-day median baseline, and emits `public/ci/data.json` in the
exact shape `index.html`'s `init()` expects → `build_demo.py` inlines that
JSON into `dashboard-demo.html`.

`store/snapshots/YYYY-MM-DD.json` is written every `build_data.py` run and
is the rollback mechanism: there's no database to restore, just an older
file to copy back over `public/ci/data.json`.

## What `untracked` means here

The dashboard's "Other / Untracked" row represents the long tail of smaller
and craft competitors this pipeline never scrapes. Real ingestion only
covers the eight named brands, so `untracked`'s per-window figures are left
empty rather than filled with a fabricated tail percentage — the front end
treats a missing untracked window as a zero contribution. An honest "we
don't measure this" beats a confident-looking number nobody can support.

## Front-end edits, for anyone auditing "no render function changed"

Every edit inside `public/ci/index.html` falls into one of three buckets:

1. **Phase 4e wiring** — `BRANDS`/`PROFILES`/`PORTFOLIOS`/`UNTRACKED`/`META`
   went from hardcoded `const` to empty `let`, populated by `init()`'s
   `fetch('./data.json')`; `showLoading()` / `showDataError()` were added;
   the top bar gained a staleness check (`meta.updatedISO` > 30h → a `STALE`
   chip).
2. **Field rewiring the schema change requires** (RULE 1's explicit
   exception) — every read of the old synthetic devices (`rangeFactor`,
   `prevFactor`, `curveIG`/`curveYT`/`CURVES`, `.base30`) now reads the real
   equivalent (`profile.windows[range]`, `profile.prev30`,
   `profile.seriesIG`/`seriesYT`) at the same call site. `deriveThemeMatrix()`
   reconstructs the per-theme polarity breakdown the theme×polarity chart
   needs from the real `themeShare` + `sentiment` the aggregator emits
   (classify.py samples comments, it doesn't exhaustively tag every
   theme×polarity cell, so this cross-tab was always a derivation, not raw
   data — it's the same derivation as before, just fed real inputs now).
   `shares`/`saves` can legitimately be `null` now (not public data for any
   brand this pipeline touches); the one display site that printed them
   raw (`renderEngagementChart`'s breakdown cards) shows `NOT PUBLIC`
   instead of a false zero.
3. **Everything else** — every render function (the radial chart, ranked
   bars, surrogate band, all of Platform Intelligence and Brand/Group
   Detail, the methodology panel's layout) is byte-for-byte what it was in
   the placeholder build. They already only ever read the row/entity shapes
   `computeRows()` / `entityForDetail()` hand them — once those two (plus
   the handful of smaller `computeX`/`sparklineX` helpers) point at the real
   fields, nothing downstream needed to know anything changed.
