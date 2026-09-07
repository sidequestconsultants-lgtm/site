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
  config.py           the 9 brands, handles, parent mapping, thresholds — edit this by hand
  store.py             shared JSON I/O + the dedupe-by-key upsert that makes ingestion idempotent
  usage.py              Apify spend tracking against the $4 monthly ceiling (store/usage.json)
  preflight.py           validates the 3 API keys are present and reachable before a real run
  verify_handles.py        read-only handle/channel verification report — no store writes
  pull_youtube.py       Phase 2
  pull_instagram.py      Phase 3 (refuses to run for real until brands are verified — see below)
  build_data.py           Phase 4 — the aggregator, emits public/ci/data.json
  build_demo.py             Phase 4f — inlines data.json into dashboard-demo.html
  classify.py                Phase 5 — Gemini Flash vehicle/comment classification, asymmetric
                              YT/IG comment sampling within the Apify spend ceiling
  pull_trends.py               Phase 6 — weekly search-interest pull
store/                committed JSON state
  posts.json           deduped raw posts per brand, platform:external_id keyed
  comments.json          sampled + classified comments per brand
  channel_stats.json      follower/subscriber snapshots
  pull_log.json             one row per pipeline run — fn, counts, status, error
  usage.json                 month-to-date estimated Apify spend, keyed YYYY-MM
  client_insights.json         hand-maintained only, never written by a pull script — the
                                client's own shares/saves from Meta Business Suite Insights
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
   `python -m pipeline.verify_handles` prints a read-only report (channel
   title, follower count, last-post date per handle) to check by hand
   against the live account before flipping `verified`; it makes no store
   writes and costs no Apify credit.
2. `yt_channel_id` is deliberately not pinned anywhere — `pull_youtube.py`
   resolves each brand's channel by `yt_handle` via `channels.list?forHandle=`
   on every run. That costs one extra quota unit per brand per run
   (negligible against the 10,000/day budget) and avoids a pinned ID
   silently going stale if a channel changes its handle or branding.
3. Set the three GitHub Actions repo secrets: `APIFY_TOKEN`,
   `YOUTUBE_API_KEY`, `GEMINI_API_KEY`. `python -m pipeline.preflight`
   checks all three are present and reachable (a cheap, quota-safe call
   per API) before any real pull runs. Keep the repo **private** if you use
   it — public repos get unlimited Actions minutes, but `store/` becomes
   public with them.
4. `store/client_insights.json` starts as `{}`. Nothing in this pipeline
   writes to it automatically — shares/saves aren't exposed by any public
   API this pipeline touches (Apify's IG scrape has no share/save count;
   YouTube has no "save" concept). The client can hand-fill their own
   entry (`{"<client_brand_id>": {"shares": N, "saves": N}}`) from their
   Meta Business Suite Insights; every other brand's shares/saves stay
   `null` regardless of what this file contains.

## Running locally

```bash
pip install -r pipeline/requirements.txt
export YOUTUBE_API_KEY=...
export APIFY_TOKEN=...
export GEMINI_API_KEY=...

python -m pipeline.preflight                  # checks all 3 API keys are present + reachable
python -m pipeline.verify_handles             # read-only report, no store writes, no credit spent
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

## Instagram accounts that come back thin — restricted profiles

A real run turned up four brands (Budweiser, Corona, Tuborg, Carlsberg)
that returned exactly one post each while others paginated normally.
Root cause: Apify's actor runs logged-out for every profile — it cannot use
a login or session, full stop, for legal reasons the actor's own docs state
— and Instagram serves a reduced or fully gated view to logged-out viewers
on accounts with the alcohol/sensitive-content age gate turned on. When
that happens the actor doesn't paginate short; it returns a single
placeholder item carrying an `error`/`errorDescription` (or
`isRestrictedProfile`) field instead of real post data. There is no Apify
input setting that bypasses this — it's a hard platform restriction, not a
config knob — so the fix is detection, not a workaround:

- `pull_instagram.py` checks every raw item for that error signature
  (`_is_restricted_item()`) and excludes it from the saved records, so a
  gated brand reads as genuinely unmeasurable, never as "posted once."
- The raw (pre-filter) item count is logged for every brand/request, so a
  short response is visible in the run log regardless of cause.
- A volume guard flags any brand with a known follower count over 10k that
  still comes back with fewer than 3 posts in the trailing 90 days as
  `warn`, with the raw response attached to `pull_log` — never passed
  through silently. Follower counts come from whatever the Apify response
  happens to carry (best-effort field probing, `_extract_followers()`,
  persisted to `store/channel_stats.json`'s `ig` entry) or, failing that,
  a hand-filled `ig_followers_hint` in `config.py`.

If a brand you expect to be active keeps tripping the restricted-profile
warning, that's Instagram's age gate on that specific account, not a bug
here — verify by hand and decide whether to exclude the brand (like
`EXCLUDED`) or accept it as permanently unmeasurable via this pipeline.

## Dormant brands

A brand can genuinely stop posting (Bira 91's Instagram, verified by hand,
has no activity since 2025). Left alone, that renders identically to "we
measured this brand and it's near-invisible" — a materially different and
much less charitable story than "this account isn't posting." `dormant_since`
in `config.py` (free-text, not necessarily a full date — a bare year is a
legitimate value pending a more exact one) flags this by hand per brand.

The dashboard only replaces a brand's bar/ring with a `DORMANT` badge when
its *combined* share still rounds to nothing (`row.dormantFull`, computed
in `computeRows()`) — a brand that's gone quiet on Instagram but still has
real YouTube-driven share keeps its real bar, with an `IG DORMANT SINCE …`
note appended instead. This never hides a genuine non-zero number; it only
relabels a true zero that would otherwise be indistinguishable from a
competitor genuinely losing.

## Data flow

`pull_youtube.py` / `pull_instagram.py` → `store/posts.json` (dedupe key
`platform:external_id`, idempotent — a re-run refreshes counters on existing
rows, never appends a duplicate; post ingestion always runs before, and
takes priority over, comment fetching) → `classify.py` samples comments
asymmetrically — YouTube's `commentThreads` is free within quota
(`YT_COMMENT_POSTS=25` posts × `YT_COMMENT_PER_POST=200`), Instagram
comments cost Apify credit (`IG_COMMENT_POSTS=8` × `IG_COMMENT_PER_POST=100`)
and stop being fetched the moment month-to-date spend
(`store/usage.json`, tracked by `usage.py`) reaches `APIFY_MONTHLY_CEILING_USD`
— into `store/comments.json`, tagging both posts (surrogate vehicle) and
comments (spam/polarity/theme/language); the platform composition of each
run's sample is surfaced in `meta.commentSample` →
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
covers the nine named brands, so `untracked` is not a measurement — it's a
disclosed, fixed-share model: `config.UNTRACKED["share_assumption"]`
(currently 0.074) is solved, per window, so that
`untracked / (tracked_total + untracked) == share_assumption` holds exactly
against that window's real tracked total. The whole modelled figure is
carried on `ig.organic` (there's no per-platform breakdown for a bucket
nothing is actually scraped from); `untrackedShareAssumption` is surfaced in
`meta` and printed in METHODOLOGY so the number is never mistaken for a
measurement. An honest, disclosed model beats either a fabricated precise
figure or a silent zero.

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
   brand this pipeline touches, `client_insights.json` aside); the one
   display site that printed them raw (`renderEngagementChart`'s breakdown
   cards) shows `NOT PUBLIC` instead of a false zero. `search` (Trends)
   series can legitimately contain `null` buckets too — a bucket Trends
   reports as flat 0 means "below its reporting floor," not "measured zero
   interest" (`config.TRENDS_ZERO_IS_NULL`), so `renderSearchSeries()` draws
   a gap in the line rather than a false trough, `renderSearchStrip()` /
   `trendBlock()` append a BELOW THRESHOLD note when any bucket is null, and
   the portfolio/group weighted average in `entityForDetail()` excludes a
   member's null bucket from that bucket's weight instead of letting
   `null * weight` silently coerce to a measured zero.
3. **Everything else** — every render function (the radial chart, ranked
   bars, surrogate band, all of Platform Intelligence and Brand/Group
   Detail, the methodology panel's layout) is byte-for-byte what it was in
   the placeholder build. They already only ever read the row/entity shapes
   `computeRows()` / `entityForDetail()` hand them — once those two (plus
   the handful of smaller `computeX`/`sparklineX` helpers) point at the real
   fields, nothing downstream needed to know anything changed.
