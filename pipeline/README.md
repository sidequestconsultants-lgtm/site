# Competitive Intelligence pipeline

Ingestion and serving layer for the live Competitive Intelligence dashboard
— currently tracking Indian QSR (quick-service restaurant) brands; see
"Category pivots" below for how a different category/client gets onto this
same pipeline. Zero paid services, no database — state lives as JSON files
in this repo, GitHub Actions runs it daily, Vercel serves the output.

The dashboard itself (`public/ci/index.html`) is fully decoupled from
`pipeline/config.py`'s brand set and category: it only ever reads the shape
`build_data.py` emits to `data.json` (`brands`/`profiles`/`portfolios`/
`untracked`/`meta`), never a brand ID or category word directly. **No
render function was touched for this pivot** beyond the field rewiring and
taxonomy-label wiring documented below.

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
  config.py           tracked brands, handles, parent mapping, taxonomy, thresholds — edit this by hand
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

## Gemini model retirement and permanent failures

`classify.py` reads the model name from `config.GEMINI_MODEL`, never
hardcodes it — Google retires Gemini model versions (`gemini-1.5-*` now
404 on every call), and a retired model is a one-line config fix, not a
code change. `preflight.py`'s Gemini check goes past bare reachability: it
calls `ListModels` and confirms `config.GEMINI_MODEL` is actually in the
returned list, because a key authenticates fine against a dead or
mistyped model name — the call itself succeeds, it's the *model* that
doesn't exist — so a bare reachability check would pass and the failure
would only surface a minute into a real `classify.py` run.

A 404 from Gemini can't succeed on retry, so neither `classify_posts()`
nor `classify_comments()` treats it like an ordinary failed batch:
`gemini_json()` raises `PermanentAPIError` for it specifically, and both
callers stop calling Gemini for the rest of the run the moment they see
one (classify_comments() also stops for every brand still to come, via a
`gemini_dead` flag — comment fetching keeps running, since that doesn't
touch Gemini at all) instead of repeating the same doomed call across
every remaining batch.

## Gemini rate limits, and a run that discarded 120 classified comments

A real run hit the free-tier Gemini quota mid-classification: `classify_posts`
processed 0 of 167 pending posts (every batch 503'd, then 429'd), then
`classify_comments` managed 120 of 337 before also hitting 429. The run
still exited 1 — at the time, `main()` required *every* job to report
`"ok"`/`"warn"`, and a job that classified nothing still reported `"error"`
as an honest per-function diagnostic — so nothing committed, including the
120 comments that did succeed. Four fixes:

1. **A 429/503 is never a reason to exit non-zero.** These are expected,
   transient conditions on a free-tier key, not a crash — `gemini_json()`
   retries either one with exponential backoff
   (`config.GEMINI_RATE_LIMIT_MAX_ATTEMPTS`, default 3;
   `config.GEMINI_RATE_LIMIT_BACKOFF_BASE_S` doubling each attempt) before
   raising `RateLimitError`, which is caught separately from
   `PermanentAPIError` in both `classify_posts()` and `classify_comments()`:
   logged as `warn`, the loop moves on to the *next* batch rather than
   aborting, since classification is already idempotent by
   `model_version` and self-heals across scheduled runs either way.
   `main()`'s exit code changed from requiring every job to succeed
   (`all(s in ("ok","warn") for s in statuses)`) to requiring only that
   *one* did (`any(...)`) — the exact incident shape (posts `"error"`,
   comments `"warn"`) now exits 0 and commits the 120 real rows, matching
   the same "only fail on total, pipeline-wide failure" rule already
   applied to `pull_instagram.py`/`pull_youtube.py`.
2. **Cheapest model that's good enough.** `config.GEMINI_MODEL` is now
   `"gemini-flash-lite-latest"` — caption/comment tagging is a simple
   classification task, not one that needs a full Flash model, and the
   lite variant's free-tier request quota is far higher, which is what
   actually matters here. `preflight.py`'s existing `ListModels` check
   validates whatever string is in `config.GEMINI_MODEL`, so this needed
   no code change, only the config value.
3. **Posts get a reserved share of the run's time budget.** Post
   classification drives the offer-mix chart — this product's
   differentiator — so `classify_posts()` runs before
   `classify_comments()` (unchanged) and additionally gets a guaranteed
   slice of wall-clock time via `config.CLASSIFY_POSTS_TIME_SHARE` (0.6):
   when both jobs run in one invocation, posts get up to
   `CLASSIFY_MAX_MINUTES * CLASSIFY_POSTS_TIME_SHARE` and comments get
   whatever remains of the overall `CLASSIFY_MAX_MINUTES` deadline,
   regardless of how long posts actually took. Either `--posts-only` or
   `--comments-only` alone gets the full budget — there's nothing to
   reserve a share from. Hitting the deadline mid-run stops cleanly
   (checked per-batch in `classify_posts()`, per-brand and per-batch in
   `classify_comments()`) and logs exactly how many posts/comments/brands
   are left unprocessed, rather than running over or silently dropping
   them; they pick up on the next scheduled run the same as any other
   still-pending record.
4. **Less load per run.** `config.YT_COMMENT_POSTS`/`PER_POST` cut from
   25×200 to 10×60 — comment classification alone was making enough
   Gemini calls to help exhaust the quota before posts got a fair share.
   `COMMENT_BATCH_SIZE` (100, vs `POST_BATCH_SIZE`'s 20) batches more
   comments per Gemini call, trading a slightly longer prompt for far
   fewer requests, which is what a per-minute rate limit actually counts.

## Instagram accounts that come back thin — restricted profiles

A real run on an earlier tracked set turned up several brands that each
returned exactly one post while others paginated normally. Root cause:
Apify's actor runs logged-out for every profile — it cannot use a login or
session, full stop, for legal reasons the actor's own docs state — and
Instagram serves a reduced or fully gated view to logged-out viewers on
accounts with a content gate turned on for a market (the concrete case
that triggered this: several alcohol brands' accounts had Instagram's
alcohol/sensitive-content age gate on; see git history for that run's
specifics). When that happens the actor doesn't paginate short; it returns
a single placeholder item carrying an `error`/`errorDescription` (or
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

## Partial pulls, credit exhaustion, and coverage-gated windows

A real run pulled 6 of 7 brands successfully, then the 7th hit an Apify
quota 403 partway through a 90-day-per-brand backfill — enough in one run
to exhaust a month's free credit — and the whole script exited non-zero,
which (GitHub Actions stops the job at the first failing step by default)
meant `build_data`/the commit step never ran and all 490 already-fetched
rows were discarded along with the one brand that failed. Four fixes:

1. **A partial pull commits what it got.** `pull_instagram.py` (and, for
   the same reason, `pull_youtube.py` and `classify.py`) now tracks
   per-brand success independently of the run's overall status.
   `store.save_posts()` runs once, unconditionally, after the loop — a
   later brand's failure never discards an earlier brand's real rows. The
   run only becomes `"error"` (the one status that fails the workflow)
   when **zero** attempted brands succeeded; any partial success is
   `"warn"` and still exits 0 (`main()`: `sys.exit(0 if status in ("ok",
   "warn") else 1)`). A quota 403 (`ApifyQuotaExceeded`) is caught
   specifically and, once seen, skips every *remaining* brand for that run
   instead of rediscovering the same exhausted credit one brand at a time.
2. **One-time 30-day backfill, then incremental forever.**
   `config.INITIAL_PULL_DAYS = 30` replaces the old 90-day first-pull
   window in `compute_since()` — a 90-day backfill across every brand at
   once is exactly what exhausted a month's credit in one run. Every run
   after the first is purely incremental (since the newest stored post,
   same as before); the store's real history keeps growing past 30 on its
   own, nothing is ever re-pulled for a period already on file.
   `config.BASELINE_DAYS` (90) is a **cap**, not an assumption — the
   anomaly model uses whatever trailing history actually exists.
   `build_data.py`'s `compute_baseline_days_actual()` records how many
   days of real history actually back a brand's paid/organic split
   (`profile.baselineDaysActual`), so that confidence is visible rather
   than silently assumed to always rest on a full window.
3. **Dashboard windows reflect actual coverage.** With 30 days of history,
   the 90-day window isn't a small number, it's an unanswerable one —
   `build_data.py`'s `compute_coverage()` finds the earliest post across
   every platform and brand combined and emits `meta.coverageDays` /
   `meta.trackingSince` (see "Coverage must reflect whichever platform has
   data, not whichever has least" below — an earlier version of this
   pooled the *weakest* platform instead, which could blank the whole
   dashboard behind one thin or empty source). Any of the three
   range presets (7/30/90) longer than that is emitted as `null` — same
   null-vs-zero convention as everywhere else in this pipeline — never a
   computed-but-wrong number. `index.html` disables a range button whose
   window is unavailable, relabels it `NEEDS <n> MORE DAYS`
   (`isRangeAvailable()`/`daysNeededFor()`), clamps `STATE.range` on load
   to the longest range that *is* available, and — if even the 7-day
   window isn't covered yet (a brand-new deployment) — shows a plain
   "NOT ENOUGH DATA YET" panel instead of attempting to render normal
   charts from nothing.
4. **An exhausted Instagram source doesn't block the pipeline.**
   `.github/workflows/daily.yml`'s "Pull Instagram" and "Classify posts and
   comments" steps run with `continue-on-error: true` — a fully exhausted
   Apify credit (every brand quota-403s, `status="error"`) or a dead
   Gemini key still lets `build_data`/`build_demo`/commit run and publish
   whatever YouTube alone provided that day. "Pull YouTube" stays a hard
   gate (RULE #7 — a bad day never overwrites yesterday's good data.json);
   it's the one source with no external credit to exhaust, so its own
   total failure is still treated as nothing worth building.

## Coverage must reflect whichever platform has data, not whichever has least

A real production store had 172 real YouTube posts across 6 brands and zero
Instagram posts (Instagram hadn't run yet), but the live dashboard showed
"0 days of real history" and blanked itself behind the "NOT ENOUGH DATA
YET" panel anyway. Two separate bugs, both in coverage:

1. **`compute_coverage()` was computing the weakest platform, not the
   deepest.** The original version grouped posts by platform, found each
   platform's own earliest post, then took the *latest* of those earliest
   dates (`max()`) as `tracking_since` — "a 90-day window blends both
   platforms, so it's only as trustworthy as the shorter of the two." That
   reasoning holds for a brand tracked on two platforms of comparable
   depth, but it means a single platform with **zero or thin** data drags
   the whole store's coverage down to near-zero, blanking every brand's
   dashboard behind a source that has nothing to do with the platform a
   viewer actually wants to look at. It rewards partial data with a worse
   outcome than no data at all: if Instagram has never run, it's absent
   from the `earliest_by_platform` dict and doesn't poison anything: but
   the moment Instagram makes even one partial pull with a recent
   `posted_at`, coverage *drops* from however many days YouTube alone
   already had down to almost nothing, which reads as `trackingSince`
   resetting itself for no reason a viewer can see. `compute_coverage()`
   now pools every platform's posts into one span and takes the single
   overall earliest `posted_at` — a platform with no data simply
   contributes nothing to that span, instead of capping it. Coverage
   still only ever grows (or holds steady) over time, and a platform
   starting or resuming contributes only its own real history, never a
   regression for everyone else's.
2. **The front end's own guard was correct — it was gating on a computed
   zero.** `isRangeAvailable()`/`renderInsufficientCoverage()` already key
   off `meta.coverageDays` alone, so fixing (1) is the whole fix: once
   coverage correctly reflects the deepest platform present instead of
   the shallowest, a brand with real YouTube history and no Instagram
   history renders normally, and the blanket "NOT ENOUGH DATA YET" panel
   only appears when truly nothing anywhere clears even the 7-day floor.

Separately, `index.html`'s `showLoading()`/`showDataError()` render the
top bar (`renderTopbar()`) before `META` is populated from the fetched
`data.json` (`META` starts as `{}`) — `${META.logoSvg}` and
`${META.updated}` in a template literal render the literal string
`"undefined"` when the field is absent, not blank. Guarded every META
field interpolated in the top bar/sidebar/print footer
(`META.logoSvg||''`, `META.updated||'—'`, `META.labels?.printTag||''`,
and a `BRANDS[CLIENT_BRAND_ID]?.name` check before the client-name
prefix) so the brief loading state — or any future build that's missing
a field — never shows the word "undefined" to a viewer.

## Multi-handle brands

`handle_ig` in `config.py` is always a list, even for the common case of
one handle — a brand can legitimately run more than one Instagram account
(different operators in different regions, say), and a single-handle brand
is just a one-element list, not a special case. `pull_instagram.py` pulls
every handle, tags each fetched post with which handle it came from, then
runs `mark_cross_handle_duplicates()`: if two of a brand's own handles post
the same creative (exact match on normalized caption, within 48 hours of
each other — deliberately strict, to keep a false match rare), the later
one is flagged `is_duplicate` rather than dropped. A flagged post's real,
separately-earned engagement still counts toward visibility in full (two
different audiences really did see and react to it); `build_data.py`
excludes it from every post-*count*-based stat instead (`aggregate_window`'s
`n_posts`, `compute_format_mix`, `compute_vehicle_mix`) — one piece of
content shouldn't inflate a "how many times did this brand post" or "what
share of posts are X" figure just because two of its own accounts carried
it. `handle_fb` is a plain string for a single-Facebook-page brand and a
list for a multi-page one — `build_data.py`'s `_as_list()` normalizes
either shape rather than assuming one.

`yt_handle` is usually an `@handle`, resolved to a channel ID via
`channels.list?forHandle=` at pull time — but a brand can instead be
hand-verified only down to the raw channel ID (`config.py` comments each
one this applies to). `pull_youtube.py`'s `_looks_like_channel_id()`
detects the `UC` + 22-character shape and calls `channels.list?id=`
directly for those, skipping the handle-resolution step entirely; both
`resolve_channel_id()` and `verify_handles.py`'s lookup dispatch on it.

## Dormant brands

A brand can genuinely stop posting on a platform. Left alone, that renders
identically to "we measured this brand and it's near-invisible" — a
materially different and much less charitable story than "this account
isn't posting." `dormant_since` in `config.py` (free-text, not necessarily
a full date — a bare year is a legitimate value pending a more exact one)
flags this by hand per brand; no brand in the current tracked set is
flagged, but the field and the render path stay in place for whenever one
is.

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
— into `store/comments.json`, tagging both posts (vehicle — see
`config.VEHICLES`/`LABELS` for what that means for the current category)
and comments (spam/polarity/theme/language); the platform composition of each
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
competitors this pipeline never scrapes. Real ingestion only covers the
brands named in `config.BRANDS`, so `untracked` is not a measurement —
it's a disclosed, fixed-share model: `config.UNTRACKED["share_assumption"]`
is solved, per window, so that
`untracked / (tracked_total + untracked) == share_assumption` holds exactly
against that window's real tracked total. The whole modelled figure is
carried on `ig.organic` (there's no per-platform breakdown for a bucket
nothing is actually scraped from); `untrackedShareAssumption` is surfaced in
`meta` and printed in METHODOLOGY so the number is never mistaken for a
measurement. An honest, disclosed model beats either a fabricated precise
figure or a silent zero.

## Category pivots (e.g. alcobev → QSR)

The front end is built so a category/client pivot is a `config.py` edit, not
a rewrite — three structural rules make that true:

1. **Nothing in `index.html` references a client or brand by literal ID.**
   `CLIENT_BRAND_ID` / `CLIENT_PORTFOLIO_ID` are resolved once on load by
   scanning `BRANDS` / `PORTFOLIOS` for `isClient===true` (`resolveClientIds()`,
   called right after `init()`'s fetch) and cached; every place that used to
   hardcode a brand ID (`headToHeadBlock`'s client-suppression and its "vs"
   comparison, the topbar client name, the Platform Intelligence headline,
   the document title) reads those two instead. Insight copy selects
   entities by rank/role (leader, client, biggest non-leader mover on a
   given metric) exclusively — never a literal ID — so a different tracked
   set changes which brand fills a sentence, never whether the sentence
   breaks. Two other spots hardcoded a brand *count* the same way a literal
   ID would (`8 TRACKED BRANDS`, `5` for groups in `denomNoteFor`) — both now
   read `Object.keys(BRANDS).length` / `Object.keys(PORTFOLIOS).length`.
2. **No category word is hardcoded in a render function.** Every
   category-facing string (axis/section labels, the vehicle-classification
   methodology heading and caveat, the print-footer tag, the untracked note)
   reads from `meta.labels` (`build_data.py`'s `build_meta()` emits
   `dict(config.LABELS)` verbatim — add the category's strings in
   `config.py`, not here). Renamed the functions/classes that read as
   beer-specific now that the concept is generic: `renderSurrogateBand` →
   `renderVehicleBand`, `surrogateMixShiftBlock` → `vehicleMixShiftBlock`,
   `.surrogate-band`/`#surrogateCard` → `.vehicle-band`/`#vehicleCard`,
   `.sband-*` → `.vband-*`.
3. **The taxonomy itself is data, not a JS constant.** `VEHICLES` and
   `THEMES` used to be hardcoded `const` arrays in `index.html` carrying
   the previous category's ids, labels, colors, and (for themes) the
   negativity-weighting constant `deriveThemeMatrix()` uses to spread
   aggregate sentiment across themes — a second, easy-to-miss hardcode
   alongside `meta.labels` above, since the old ids (`soda`, `availability`,
   …) don't read as beer-specific at a glance. Both are now `let`,
   populated in `init()` from `meta.vehicles`/`meta.themes`
   (`build_data.py`'s `build_meta()` assembles them from
   `config.VEHICLES`/`THEMES` + `VEHICLE_LABELS`/`VEHICLE_COLOR_VARS`/
   `THEME_LABELS`/`THEME_LIFT`/`THEME_OUTLIER_CAPTIONS`). A pivot edits
   those config dicts (plus the matching `--v-*` CSS vars in `index.html`'s
   `:root` — colors are the one piece of this still hand-paired, see the
   comment above that block) and never touches a render function. The
   `classify.py` prompts that describe what each vehicle/theme value means
   to the LLM are a fourth place a pivot must edit by hand — schema-driven
   (`config.VEHICLES`/`THEMES`), but the prose description of each value
   is necessarily hand-written per category.

**Acceptance test for rule 1** (run this after any pivot): rename every
brand ID in `data.json` to `brand_a`…`brand_g`, set `isClient` on one, and
confirm every view renders with no console errors and head-to-head is
intact for non-client brands and suppressed for the client.

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
   bars, vehicle band, all of Platform Intelligence and Brand/Group
   Detail, the methodology panel's layout) is byte-for-byte what it was in
   the placeholder build. They already only ever read the row/entity shapes
   `computeRows()` / `entityForDetail()` hand them — once those two (plus
   the handful of smaller `computeX`/`sparklineX` helpers) point at the real
   fields, nothing downstream needed to know anything changed.
