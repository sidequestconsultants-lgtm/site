"""
Brand configuration — QSR Competitive Intelligence (India).

PIVOT FROM ALCOBEV. Reason: four of nine beer brands age-gate their Instagram,
and Apify runs logged-out by design with no way around it. QSR has no age gates,
posts at high volume, and Trends works properly for these brands.

Handles marked verified: True were supplied by hand. Handles marked False are
INFERRED and must be checked in a browser before any real pull — pull_instagram.py
refuses to run while any brand is unverified. Do not guess a handle: the beer set
had @kingofgoodtimes for Kingfisher and "Budweiser Experiences" for Budweiser.
Naming conventions do not hold.

`handle_ig` is ALWAYS a list, even for a single-handle brand — McDonald's runs
two accounts (Westlife Foodworld West/South, CPRL North/East) and is the only
brand with more than one; every consumer must iterate, dedupe cross-posted
content, and sum. `handle_fb` is a plain string except for McDonald's, which
is also a list there.

`ig_followers_hint` — optional, hand-verified approximate IG follower count
(summed across handles for a multi-handle brand). pull_instagram.py's
under-fetch volume guard prefers a freshly scraped follower count when the
actor's response happens to carry one, and falls back to this when it
doesn't. Leave `None` until hand-checked.

`dormant_since` — optional, hand-verified free-text note for a brand with no
recent Instagram activity, rendered as DORMANT instead of a competitor sitting
at ~0% SOV. None of the brands below are known dormant; left structurally
available in case that changes.
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

BRANDS = {
    "kfc": {
        "name": "KFC",
        "parent": "yum",
        "handle_ig": ["kfcindia_official"],
        "yt_handle": "UCg5ukNutGtg1KqvWwuc56xw",   # channel ID, not a handle
        "handle_fb": "KFC-India-61563476804822",
        "is_client": True,
        "color_var": "--c-kfc",
        "trends_query": "KFC India + KFC near me + KFC menu + KFC offer + KFC coupon",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
    "pizzahut": {
        "name": "Pizza Hut",
        "parent": "yum",
        "handle_ig": ["pizzahut_india"],
        "yt_handle": "UCOBjFMnb_0rfwV0plAYXsfQ",
        "handle_fb": "pizzahutindia",
        "is_client": False,
        "color_var": "--c-pizzahut",
        "trends_query": "Pizza Hut India + Pizza Hut near me + Pizza Hut menu + Pizza Hut offer",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
    "tacobell": {
        "name": "Taco Bell",
        "parent": "yum",
        "handle_ig": ["tacobellindia"],
        "yt_handle": "UCOjKPr9SdoKhZHZ7CDdg_jg",
        "handle_fb": "tacobellindia",
        "is_client": False,
        "color_var": "--c-tacobell",
        "trends_query": "Taco Bell India + Taco Bell near me + Taco Bell menu + Taco Bell offer",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
    "mcdonalds_in": {
        "name": "McDonald's",
        "parent": "mcdonalds",
        # TWO accounts, one brand. India is split between operators —
        # Westlife Foodworld (West & South) and CPRL (North & East) — but it is
        # one brand to a consumer and one brand in search. Aggregated.
        # This is the ONLY brand with more than one handle; the asymmetry is
        # deliberate and must be stated in METHODOLOGY.
        "handle_ig": ["mcdonalds_india", "mcdonaldsinindia"],
        "yt_handle": "UCaj66rhgdjzNmIQ6rtcFxzw",
        "handle_fb": ["McDonaldsIndia", "McDonaldsinIndia"],
        "is_client": False,
        "color_var": "--c-mcdonalds",
        "trends_query": "McDonalds India + McDonalds near me + McDonalds menu + McDonalds offer",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
    "burgerking": {
        "name": "Burger King",
        "parent": "rbi",
        "handle_ig": ["burgerkingindia"],
        "yt_handle": None,
        "handle_fb": "burgerkingindia",
        "is_client": False,
        "color_var": "--c-burgerking",
        "trends_query": "Burger King India + Burger King near me + Burger King menu + BK offer",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
    "dominos": {
        "name": "Domino's",
        "parent": "jubilant",
        "handle_ig": ["dominos_india"],
        "yt_handle": "@DominosPizzaIndia",
        "handle_fb": "dominospizzaindia",
        "is_client": False,
        "color_var": "--c-dominos",
        "trends_query": "Dominos India + Dominos near me + Dominos menu + Dominos offer",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
    "subway": {
        "name": "Subway",
        "parent": "subway_group",
        "handle_ig": ["subway_india"],
        "yt_handle": "@SubwayIndiaSocial",
        "handle_fb": "SubwayIndia",
        "is_client": False,
        "color_var": "--c-subway",
        "trends_query": "Subway India + Subway near me + Subway menu + Subway offer",
        "verified": True,
        "ig_followers_hint": None,
        "dormant_since": None,
    },
}

# ── Portfolio rollup ──────────────────────────────────────────────────────────
# YUM! is the client group and the strongest demonstration of the lens: KFC,
# Pizza Hut and Taco Bell compete separately but roll into one owner, and that
# combined position is invisible at brand level.

PORTFOLIOS = {
    "yum": {
        "name": "Yum! Brands",
        "members": ["kfc", "pizzahut", "tacobell"],
        "color_var": "--c-kfc",
        "is_client": True,
    },
    "mcdonalds": {
        "name": "McDonald's Corp",
        "members": ["mcdonalds_in"],
        "color_var": "--c-mcdonalds",
        "is_client": False,
    },
    "rbi": {
        "name": "Restaurant Brands Intl",
        "members": ["burgerking"],
        "color_var": "--c-burgerking",
        "is_client": False,
    },
    "jubilant": {
        "name": "Jubilant FoodWorks",
        "members": ["dominos"],
        "color_var": "--c-dominos",
        "is_client": False,
    },
    "subway_group": {
        "name": "Subway",
        "members": ["subway"],
        "color_var": "--c-subway",
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
    "share_assumption": 0.112,
    "note": "Regional QSR and cloud kitchens outside the tracked set. Modelled.",
}

# ── Handles dropped, with reasons — keep for METHODOLOGY ──────────────────────

EXCLUDED = {}

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
# QSR comments run far higher volume than alcobev and are dominated by complaints
# and order issues. Expect a LOWER spam rate and a much higher service-theme share.

YT_COMMENT_POSTS = 25
YT_COMMENT_PER_POST = 200
IG_COMMENT_POSTS = 8
IG_COMMENT_PER_POST = 100

# ── Spend ceiling ─────────────────────────────────────────────────────────────
# Free Apify credit is $5/month. Post ingestion ALWAYS has priority over comment
# fetching — if the ceiling is hit, skip IG comments, log warn, continue.

APIFY_MONTHLY_CEILING_USD = 4.00
USAGE_FILE = "store/usage.json"

# ── Gemini ────────────────────────────────────────────────────────────────────
# gemini-1.5-* are shut down and return 404. Keep the model name here, never in
# classify.py, and have preflight.py validate it against ListModels.
GEMINI_MODEL = "gemini-3.7-flash"

# ── Vehicles and themes ───────────────────────────────────────────────────────
# "Vehicle" here means offer type, not surrogate-ad vehicle — the word stays
# generic in code (config.VEHICLES) on purpose; what it means for a given
# category lives entirely in this list + the classification prompt in
# classify.py + meta.labels below, nowhere else.

VEHICLES = [
    "new_launch",       # new product or permanent menu addition
    "value_offer",      # price, combo, discount, coupon
    "lto",              # limited time offer, seasonal, festival
    "brand",            # lifestyle, culture, sponsorship, no product push
    "delivery",         # Swiggy / Zomato / own-app partnership or push
    "csr",              # sustainability, sourcing, community
    "unclassified",
]

THEMES = ["taste", "price", "service", "delivery", "hygiene", "other"]

# Display metadata for VEHICLES/THEMES — labels, CSS color vars (defined in
# index.html's :root — update both together when changing a category's
# taxonomy), and per-theme negativity weighting for deriveThemeMatrix()'s
# modelled theme×polarity split (classify.py tags one polarity per comment,
# not per theme, so the front end spreads the aggregate sentiment across
# themes by how negatively that theme's complaints typically skew). All of
# it is category judgment, so it lives here, never hardcoded in index.html.
VEHICLE_LABELS = {
    "new_launch": "NEW LAUNCH",
    "value_offer": "VALUE OFFER",
    "lto": "LIMITED TIME",
    "brand": "BRAND",
    "delivery": "DELIVERY",
    "csr": "CSR",
    "unclassified": "UNCLASSIFIED",
}
VEHICLE_COLOR_VARS = {
    "new_launch": "--v-new_launch", "value_offer": "--v-value_offer", "lto": "--v-lto",
    "brand": "--v-brand", "delivery": "--v-delivery", "csr": "--v-csr", "unclassified": "--v-unclassified",
}
THEME_LABELS = {
    "taste": "TASTE", "price": "PRICE", "service": "SERVICE",
    "delivery": "DELIVERY", "hygiene": "HYGIENE", "other": "OTHER",
}
# Hygiene and service complaints run most negative in QSR comment sections;
# taste complaints are more mixed (plenty of praise alongside complaints).
THEME_LIFT = {
    "hygiene": 2.0, "service": 1.6, "delivery": 1.4, "price": 1.1, "taste": 0.7, "other": 1.0,
}

# Illustrative outlier-post captions for the Brand/Group Detail page's
# "Flagged Posts" card — one per theme, {region} filled in from a fixed
# city list at render time. Flavour text, not real post data (this pipeline
# doesn't fetch or display actual flagged post content); still category
# judgment, so it belongs here, not hardcoded in index.html.
THEME_OUTLIER_CAPTIONS = {
    "taste": "complaints about a recipe or formulation change drew an unusual negative wave",
    "price": "pricing backlash after a menu price revision reported out of {region}",
    "service": "service-speed and order-accuracy complaints spiked out of {region}",
    "delivery": "delivery-partner complaints (late, cold, wrong order) spiked out of {region}",
    "hygiene": "a hygiene or cleanliness complaint went semi-viral out of {region}",
    "other": "a repost/meme thread drew an unusual negative comment wave",
}

# ── Trends ────────────────────────────────────────────────────────────────────
# geo=IN always. Max 5 terms per request — run overlapping batches sharing the
# anchor and rescale. Each query capped at 100 CHARACTERS including "+" joins.
#
# QSR SEARCH IS MOSTLY TRANSACTIONAL, NOT BRAND INTEREST. Queries blend three
# intents per brand: brand, location/menu ("near me", "menu"), and offer
# ("offer", "coupon"). Blending means the series measures total demand but CANNOT
# separate "interest is up" from "people are hunting discounts". If that
# distinction matters later, split into two series per brand — at the cost of
# doubling requests and compounding rescale error.
#
# BIGGEST BLIND SPOT IN THIS CATEGORY: Swiggy and Zomato in-app search never
# touches Google. For QSR that is likely the majority of purchase intent. State
# this in METHODOLOGY — it is a larger gap here than it was for alcobev.
TRENDS_ANCHOR = "kfc"
TRENDS_GEO = "IN"
TRENDS_TIMEZONE = 330
TRENDS_ZERO_IS_NULL = True


def unverified_brands():
    return [bid for bid, b in BRANDS.items() if not b.get("verified")]


def client_brand_id():
    for bid, b in BRANDS.items():
        if b.get("is_client"):
            return bid
    raise RuntimeError("no brand flagged is_client in config.py")


# ── Methodology constants carried over from the pre-pivot config ──────────────
# (CPM/format-multiplier/logo — category-neutral, untouched by this rewrite.
# META_STRINGS/LABELS below ARE category-specific and are rewritten per pivot.)

CPM = {"instagram": 182, "youtube": 227}
FORMAT_MULTIPLIER = {"video": 1.24, "mixed": 1.00, "static": 0.86}
STALENESS_HOURS = 30
SPAM_RATE_BASE = 0.61

# Every category-facing string a render function needs — a pivot edits this
# dict (and META_STRINGS below), never public/ci/index.html. See
# pipeline/README.md's "Category pivots" section for the contract.
LABELS = {
    "vehicleAxis": "OFFER TYPE",
    "vehicleSplitLabel": "OFFER MIX",
    "vehicleShiftLabel": "OFFER MIX — SHIFT ACROSS WINDOW",
    "vehicleMethodology": "OFFER TYPES",
    "vehicleCaveat": "CONTENT CLASSIFIED BY OFFER TYPE — LAUNCH, VALUE, LTO, BRAND, DELIVERY, CSR.",
    "printTag": "OFFER-CLASSIFIED",
    "untrackedNote": "UNTRACKED HAS NO OFFER CLASSIFICATION",
}

META_STRINGS = {
    "metaAdNote": (
        "Meta's Ad Library API returns only political and social-issue ads outside the "
        "EU and UK, and does not expose spend for commercial advertisers anywhere. No "
        "measured spend figure is obtainable for this category. All expense values are "
        "modelled from public impression proxies and published CPM benchmarks."
    ),
    "viewProxyCaveat": "VIEW-BASED PROXY · SHORT-FORM LOOPING CONTENT INFLATES COUNTS · NOT REACH",
    "searchCaveat": "SEARCH INTEREST · RELATIVE INDEX 0–100 · NOT COMPARABLE TO SOV SCALE",
    "soeTwoLayerNote": (
        "SOE is modelled from a modelled input: paid/organic split is itself an estimate "
        "(views vs. a trailing-90-day median baseline), then converted to spend via CPM and "
        "format-mix assumptions. Two layers of estimation stack here — flagged, not hidden."
    ),
    "demandBlindSpotNote": (
        "Swiggy and Zomato in-app search never touches Google, and for QSR that is plausibly "
        "the majority of purchase intent. This pipeline has no visibility into it at all — a "
        "larger gap here than it was for alcobev, where on-premise and retail discovery "
        "weren't dominated by a couple of apps this way."
    ),
    "searchBlendedIntentNote": (
        "Each brand's Trends query blends three intents — brand name, location/menu (\"near "
        "me\", \"menu\"), and offer (\"offer\", \"coupon\") — to stay above Google's reporting "
        "floor. That means the series measures total demand but cannot separate rising brand "
        "interest from discount-hunting; a spike could be either."
    ),
    "mcdonaldsHandleNote": (
        "McDonald's India runs two Instagram accounts — @mcdonalds_india (Westlife Foodworld, "
        "West & South) and @mcdonaldsinindia (CPRL, North & East) — operated by different "
        "franchisees but one brand to a consumer and one brand in search. Both are pulled and "
        "rolled into a single McDonald's profile; a post cross-published to both accounts is "
        "deduped on caption + timestamp proximity so it counts once, not twice, in every "
        "post-count-based stat, while its real engagement from both audiences still counts in "
        "full toward visibility. McDonald's is the only multi-handle brand in the tracked set."
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
