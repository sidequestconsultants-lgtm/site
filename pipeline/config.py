"""
Brand configuration — Kingfisher Competitive Intelligence.

Instagram handles hand-verified 07 SEP 2026.
YouTube + Facebook handles hand-verified 07 SEP 2026 where present.
Null handles are genuinely unresolved, not errors: pull scripts must SKIP and
log them, never fail the run. Fill them in later without touching anything else.

YouTube handles resolve to channel IDs via channels.list?forHandle= at pull time.
Note they do NOT follow the Instagram naming pattern — Kingfisher is
@kingofgoodtimes, Budweiser is "Budweiser Experiences". Never guess a handle.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORE_DIR = REPO_ROOT / "store"
SNAPSHOTS_DIR = STORE_DIR / "snapshots"
PUBLIC_DIR = REPO_ROOT / "public" / "ci"

POSTS_PATH = STORE_DIR / "posts.json"
COMMENTS_PATH = STORE_DIR / "comments.json"
PULL_LOG_PATH = STORE_DIR / "pull_log.json"
TRENDS_PATH = STORE_DIR / "trends.json"
# Hand-maintained only — no pull script writes here. The client fills in
# their own shares/saves from Meta Business Suite Insights (an authenticated
# source no scraper in this pipeline has access to); everyone else's
# shares/saves stay null regardless of what this file contains.
CLIENT_INSIGHTS_PATH = STORE_DIR / "client_insights.json"

DATA_JSON_PATH = PUBLIC_DIR / "data.json"
DASHBOARD_LIVE_PATH = PUBLIC_DIR / "index.html"
DASHBOARD_DEMO_PATH = REPO_ROOT / "dashboard-demo.html"

# ── Brands ────────────────────────────────────────────────────────────────────
# One handle per brand. Sub-brands with their own handles are tracked as separate
# brands rather than aggregated, so that no brand gets more handles than another.
# This symmetry is a methodology commitment — state it in METHODOLOGY.

BRANDS = {
    "kingfisher": {
        "name": "Kingfisher",
        "parent": "unitedbreweries",
        "handle_ig": "kingfisherworld",
        "yt_handle": "@kingofgoodtimes",
        "handle_fb": "kingfisher",
        "is_client": True,
        "color_var": "--c-kingfisher",
        "trends_query": "Kingfisher beer + Kingfisher Premium + Kingfisher Strong + Kingfischer + किंगफिशर बियर",
        "verified": True,
    },
    "kingfisher_ultra": {
        "name": "Kingfisher Ultra",
        "parent": "unitedbreweries",
        "handle_ig": "kingfisherultra",
        # Channel is branded "Kingfisher Ultra Premium Soda" — a surrogate vehicle,
        # not a beer channel. Expect near-total SODA/WATER classification. This is
        # the brand's actual YouTube presence and belongs in the set.
        "yt_handle": "@TheKingfisherUltraPremiumSoda",
        "handle_fb": None,
        "is_client": False,          # client family, but not the client brand
        "color_var": "--c-kfultra",
        "trends_query": "Kingfisher Ultra + KF Ultra + Ultra Max + Kingfischer Ultra + किंगफिशर अल्ट्रा",
        "verified": True,
    },
    "heineken_india": {
        "name": "Heineken",
        # Heineken NV holds the controlling stake in United Breweries and the
        # brand is brewed and distributed through UB in India. Grouped under
        # unitedbreweries for an India-market view. Judgement call — stated in
        # METHODOLOGY so it can be challenged.
        "parent": "unitedbreweries",
        "handle_ig": "heineken_india",
        "yt_handle": None,
        "handle_fb": "heinekenIND",
        "is_client": False,
        "color_var": "--c-heineken",
        "trends_query": "Heineken + Heiniken + Hineken + Heinken + हेनेकेन",
        "verified": True,
    },
    "budweiser": {
        "name": "Budweiser",
        "parent": "abinbev",
        "handle_ig": "budweiserindia",
        "yt_handle": "@budweiserindia",
        "handle_fb": "budweiser",
        "is_client": False,
        "color_var": "--c-budweiser",
        "trends_query": "Budweiser + Budwiser + Budweizer + Bud Magnum + बडवाइज़र",
        "verified": True,
    },
    "corona": {
        "name": "Corona",
        "parent": "abinbev",
        "handle_ig": "corona_india",
        "yt_handle": None,
        "handle_fb": "coronainindia",
        "is_client": False,
        "color_var": "--c-corona",
        # NEVER query bare "Corona" — the series is dominated by the virus.
        "trends_query": "Corona beer + Corona Extra + Karona beer + कोरोना बियर",
        "verified": True,
    },
    "tuborg": {
        "name": "Tuborg",
        "parent": "carlsberg_group",
        "handle_ig": "tuborg_india",
        "yt_handle": "@tuborgindia",
        "handle_fb": None,
        "is_client": False,
        "color_var": "--c-tuborg",
        "trends_query": "Tuborg + Tuborge + Tubourg + Tuborg Classic + टुबोर्ग",
        "verified": True,
    },
    "carlsberg": {
        "name": "Carlsberg",
        "parent": "carlsberg_group",
        "handle_ig": "carlsbergindia",
        "yt_handle": "@carlsberg_india",
        "handle_fb": "carlsbergindia",
        "is_client": False,
        "color_var": "--c-carlsberg",
        "trends_query": "Carlsberg + Carlsburg + Karlsberg + Carlsberg Elephant + कार्ल्सबर्ग",
        "verified": True,
    },
    "bira91": {
        "name": "Bira 91",
        "parent": "b9beverages",
        "handle_ig": "bira91beer",
        "yt_handle": "@bira91beer",
        "handle_fb": "bira91beer",
        "is_client": False,
        "color_var": "--c-bira",
        "trends_query": "Bira 91 + Bira beer + Bira + Bira91 + बीरा बियर",
        "verified": True,
    },
    "simba": {
        "name": "Simba",
        "parent": "simba_group",
        "handle_ig": "roarwithsimba",
        "yt_handle": "@roarwithsimba007",
        "handle_fb": None,
        "is_client": False,
        "color_var": "--c-simba",
        "trends_query": "Simba beer + Simba Wit + Simba Stout + Simmba beer + सिम्बा बियर",
        "verified": True,
    },
}

# ── Portfolio rollup ──────────────────────────────────────────────────────────
# 8 brands → 5 groups. United Breweries carries YOU in portfolio lens.

PORTFOLIOS = {
    "unitedbreweries": {
        "name": "United Breweries",
        "members": ["kingfisher", "kingfisher_ultra", "heineken_india"],
        "color_var": "--c-kingfisher",
        "is_client": True,
    },
    "abinbev": {
        "name": "AB InBev India",
        "members": ["budweiser", "corona"],
        "color_var": "--c-budweiser",
        "is_client": False,
    },
    "carlsberg_group": {
        "name": "Carlsberg India",
        "members": ["tuborg", "carlsberg"],
        "color_var": "--c-tuborg",
        "is_client": False,
    },
    "b9beverages": {
        "name": "B9 Beverages",
        "members": ["bira91"],
        "color_var": "--c-bira",
        "is_client": False,
    },
    "simba_group": {
        "name": "Simba",
        "members": ["simba"],
        "color_var": "--c-simba",
        "is_client": False,
    },
}

# ── Untracked tail ────────────────────────────────────────────────────────────
# Market-universe bucket. Never a competitor, never rolls into a portfolio,
# never gets a radial ring. Appears in the SOV denominator and as a muted bar.
# Held at a fixed share until a wider market estimate exists — flagged MODELLED.

UNTRACKED = {
    "id": "untracked",
    "name": "Other / Untracked",
    "color_var": "--c-untracked",
    "share_assumption": 0.074,
    "note": "Craft and regional brands outside the tracked set. Modelled, not measured.",
}

# ── Handles dropped, with reasons — keep for METHODOLOGY ──────────────────────

EXCLUDED = {
    "haywards": "No active Instagram presence found (verified 07 SEP 2026). "
                "Excluded rather than tracked at zero.",
}

# ── Windows and thresholds ────────────────────────────────────────────────────

WINDOWS_DAYS = [7, 30, 90]
BASELINE_DAYS = 90          # trailing window for the paid/organic anomaly baseline
REFETCH_DAYS = 10           # only re-poll counts on posts newer than this
SERIES_BUCKETS = 6          # points in seriesIG / seriesYT

# Paid/organic estimation. Public data cannot distinguish promoted posts; a post
# exceeding its account's organic baseline by this multiple has the excess
# attributed to paid. Surfaced as meta.anomalyThreshold and printed in METHODOLOGY.
ANOMALY_THRESHOLD = 1.8

# Classification confidence floor. Below this, vehicle = "unclassified".
# Never force a bucket — an honest unclassified sliver beats a false bar.
VEHICLE_CONFIDENCE_FLOOR = 0.7

# ── Comment sampling ──────────────────────────────────────────────────────────
# YouTube commentThreads is free within quota; Instagram comments cost Apify
# credit. Sample asymmetrically and print the composition in meta.commentSample.

YT_COMMENT_POSTS = 25
YT_COMMENT_PER_POST = 200
IG_COMMENT_POSTS = 8
IG_COMMENT_PER_POST = 100

# ── Spend ceiling ─────────────────────────────────────────────────────────────
# Free Apify credit is $5/month. Post ingestion ALWAYS has priority over comment
# fetching — if the ceiling is hit, skip IG comments, log warn, continue.

APIFY_MONTHLY_CEILING_USD = 4.00
USAGE_FILE = "store/usage.json"

# ── Vehicles and themes ───────────────────────────────────────────────────────

VEHICLES = ["soda", "nonalc", "music", "merch", "direct", "unclassified"]
THEMES = ["availability", "price", "taste", "events", "nostalgia", "other"]

# ── Trends ────────────────────────────────────────────────────────────────────
# Max 5 terms per request. Run overlapping batches sharing an anchor, rescale.
#
# NOTE ON QUERY STRINGS: geo is already IN, so do NOT append "India" to a term.
# Doing so narrows the query to people literally typing "Budweiser India",
# which is a fraction of the volume and can flatten the series to noise.
# Add a disambiguator ONLY where the bare term is contaminated:
#   Kingfisher -> airline + bird        => "Kingfisher beer"
#   Corona     -> the virus, dominant   => "Corona beer"
#   Simba      -> The Lion King         => "Simba beer"
# Everything else runs bare.

TRENDS_ANCHOR = "kingfisher"
TRENDS_GEO = "IN"          # India only. Never run without geo — global series is meaningless here.
TRENDS_TIMEZONE = 330      # IST offset in minutes

# The "+" operator ORs terms into ONE series and costs one slot of the 5-term cap.
#
# KNOWN OVERLAP — state in METHODOLOGY:
# Kingfisher and Kingfisher Ultra are tracked as separate brands, but a query like
# "Kingfisher Ultra beer" broad-matches BOTH the Kingfisher series (contains
# kingfisher + beer) and the Ultra series. That volume is double counted. It is a
# small share of total and cannot be eliminated without exact-phrase matching,
# which would lose far more volume than it saves.
#
# TRENDS RETURNS 0 BELOW A REPORTING FLOOR. A flat zero series means "under
# Google's threshold", NOT "no interest". Record threshold-zeros distinctly and
# render them as BELOW THRESHOLD — never as a flat line, which reads as measured.
TRENDS_ZERO_IS_NULL = True

# QUERY CONSTRUCTION
# Google Trends caps each search term at 100 CHARACTERS including the "+" joins.
# Every query above is under that ceiling — check before adding terms.
# Each query bundles: primary term, key sub-variants, common misspellings, and
# the Devanagari form. Misspellings and Devanagari are included deliberately:
# excluding them systematically understates brands in a market where a large
# share of search is non-English or transliterated.
# Devanagari terms are disambiguated where the bare form is contaminated —
# कोरोना alone returns the virus, so the query uses कोरोना बियर.


def unverified_brands():
    return [bid for bid, b in BRANDS.items() if not b.get("verified")]


def client_brand_id():
    for bid, b in BRANDS.items():
        if b.get("is_client"):
            return bid
    raise RuntimeError("no brand flagged is_client in config.py")


# ── Methodology constants carried over from the pre-go-live config ────────────
# (CPM/format-multiplier/logo/caveat strings — untouched by this rewrite, still
# read by build_data.py's build_meta() and unrelated to the brand-set changes.)

CPM = {"instagram": 182, "youtube": 227}
FORMAT_MULTIPLIER = {"video": 1.24, "mixed": 1.00, "static": 0.86}
STALENESS_HOURS = 30
SPAM_RATE_BASE = 0.61

META_STRINGS = {
    "metaAdNote": (
        "Meta's Ad Library API returns only political and social-issue ads outside the "
        "EU and UK, and does not expose spend for commercial advertisers anywhere. No "
        "measured spend figure is obtainable for this category. All expense values are "
        "modelled from public impression proxies and published CPM benchmarks."
    ),
    "viewProxyCaveat": "VIEW-BASED PROXY · SHORT-FORM LOOPING CONTENT INFLATES COUNTS · NOT REACH",
    "surrogateCaveat": "INDIAN ALCOBEV — MEASURED CONTENT IS PREDOMINANTLY SURROGATE. SEE SURROGATE SPLIT.",
    "searchCaveat": "SEARCH INTEREST · RELATIVE INDEX 0–100 · NOT COMPARABLE TO SOV SCALE",
    "trendsOverlapNote": (
        "Kingfisher and Kingfisher Ultra are tracked as separate brands, but a query like "
        "\"Kingfisher Ultra beer\" broad-matches both the Kingfisher series (which contains "
        "kingfisher + beer) and the Ultra series — that volume is double counted. It is a "
        "small share of total and cannot be eliminated without exact-phrase matching, which "
        "would lose far more volume than it saves."
    ),
    "soeTwoLayerNote": (
        "SOE is modelled from a modelled input: paid/organic split is itself an estimate "
        "(views vs. a trailing-90-day median baseline), then converted to spend via CPM and "
        "format-mix assumptions. Two layers of estimation stack here — flagged, not hidden."
    ),
}

LOGO_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M12 1.5 22 7v10l-10 5.5L2 17V7L12 1.5Z" stroke="url(#lg)" stroke-width="1.3"/>'
    '<circle cx="12" cy="12" r="3.1" fill="var(--cyan)"/>'
    '<defs><linearGradient id="lg" x1="2" y1="1.5" x2="22" y2="22.5">'
    '<stop stop-color="var(--violet)"/><stop offset="1" stop-color="var(--cyan)"/>'
    '</linearGradient></defs></svg>'
)
