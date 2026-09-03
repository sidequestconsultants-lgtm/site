"""
Single source of truth for the Kingfisher CI pipeline: brands, handles, parent
mapping, colour vars, thresholds, Trends queries. This is the only file meant
to be edited by hand.

`verified` gates ingestion. Every brand starts unverified — `pull_instagram.py`
refuses to run while any brand is unverified (see RULES in the build prompt).
Flip a brand to True only after confirming its handles against the live
Instagram/YouTube accounts by hand; brands run multiple regional and sub-brand
accounts, and a wrong handle silently produces wrong data for that brand.
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

DATA_JSON_PATH = PUBLIC_DIR / "data.json"
DASHBOARD_LIVE_PATH = PUBLIC_DIR / "index.html"
DASHBOARD_DEMO_PATH = REPO_ROOT / "dashboard-demo.html"

# ── brands ──────────────────────────────────────────────────────────────
# handles_ig / yt_handle are the EXPECTED accounts, pending hand verification
# (see module docstring). yt_channel_id is left None until resolved via
# channels.list?forHandle=<yt_handle> and pinned by hand — resolving by
# handle on every run is an extra quota unit and a channel can rename its
# handle without changing its ID, so the ID is the thing worth verifying and
# freezing.
BRANDS = {
    "kingfisher": {
        "name": "Kingfisher",
        "parent": "unitedbreweries",
        "color": "var(--c-kingfisher)",
        "is_client": True,
        "handles_ig": ["kingfisherworld"],
        "yt_handle": "@KingfisherWorld",
        "yt_channel_id": None,
        "format_mix": "mixed",
        "trends_query": "Kingfisher beer",
        "verified": False,
    },
    "budweiser": {
        "name": "Budweiser",
        "parent": "abinbev",
        "color": "var(--c-budweiser)",
        "is_client": False,
        "handles_ig": ["budweiserindia"],
        "yt_handle": "@BudweiserIndia",
        "yt_channel_id": None,
        "format_mix": "video",
        "trends_query": "Budweiser India",
        "verified": False,
    },
    "tuborg": {
        "name": "Tuborg",
        "parent": "carlsbergindia",
        "color": "var(--c-tuborg)",
        "is_client": False,
        "handles_ig": ["tuborgindia"],
        "yt_handle": "@TuborgIndia",
        "yt_channel_id": None,
        "format_mix": "mixed",
        "trends_query": "Tuborg India",
        "verified": False,
    },
    "bira91": {
        "name": "Bira 91",
        "parent": "b9",
        "color": "var(--c-bira91)",
        "is_client": False,
        "handles_ig": ["bira91"],
        "yt_handle": "@Bira91",
        "yt_channel_id": None,
        "format_mix": "video",
        "trends_query": "Bira 91 beer",
        "verified": False,
    },
    "corona": {
        "name": "Corona",
        "parent": "abinbev",
        "color": "var(--c-corona)",
        "is_client": False,
        "handles_ig": ["coronaindia"],
        "yt_handle": "@CoronaIndia",
        "yt_channel_id": None,
        "format_mix": "video",
        "trends_query": "Corona beer India",
        "verified": False,
    },
    "carlsberg": {
        "name": "Carlsberg",
        "parent": "carlsbergindia",
        "color": "var(--c-carlsberg)",
        "is_client": False,
        "handles_ig": ["carlsbergindia"],
        "yt_handle": "@CarlsbergIndia",
        "yt_channel_id": None,
        "format_mix": "mixed",
        "trends_query": "Carlsberg India",
        "verified": False,
    },
    "haywards5000": {
        "name": "Haywards 5000",
        "parent": "abinbev",
        "color": "var(--c-haywards5000)",
        "is_client": False,
        "handles_ig": ["haywards5000"],
        "yt_handle": "@Haywards5000",
        "yt_channel_id": None,
        "format_mix": "static",
        "trends_query": "Haywards 5000 beer",
        "verified": False,
    },
    "simba": {
        "name": "Simba",
        "parent": "simba",
        "color": "var(--c-simba)",
        "is_client": False,
        "handles_ig": ["simbabeer"],
        "yt_handle": "@SimbaBeer",
        "yt_channel_id": None,
        "format_mix": "static",
        "trends_query": "Simba beer India",
        "verified": False,
    },
}

PORTFOLIOS = {
    "unitedbreweries": {"name": "United Breweries", "members": ["kingfisher"], "color": "var(--c-kingfisher)", "is_client": True},
    "abinbev": {"name": "AB InBev India", "members": ["budweiser", "corona", "haywards5000"], "color": "var(--c-budweiser)"},
    "carlsbergindia": {"name": "Carlsberg India", "members": ["tuborg", "carlsberg"], "color": "var(--c-tuborg)"},
    "b9": {"name": "B9 Beverages", "members": ["bira91"], "color": "var(--c-bira91)"},
    "simba": {"name": "Simba", "members": ["simba"], "color": "var(--c-simba)"},
}

UNTRACKED = {"id": "untracked", "name": "Other / Untracked", "color": "var(--c-untracked)"}

VEHICLES = ["soda", "nonalc", "music", "merch", "direct", "unclassified"]
THEMES = ["availability", "price", "taste", "events", "nostalgia", "other"]

# ── methodology constants, surfaced verbatim in meta ───────────────────
CPM = {"instagram": 182, "youtube": 227}
FORMAT_MULTIPLIER = {"video": 1.24, "mixed": 1.00, "static": 0.86}
ANOMALY_THRESHOLD = 1.8          # views > baseline * this => the excess is paid_est
SPAM_RATE_BASE = 0.61            # category baseline printed in METHODOLOGY until real samples land
CLASSIFY_CONFIDENCE_FLOOR = 0.7  # below this a post is forced to 'unclassified', never guessed
INSTAGRAM_REFRESH_WINDOW_DAYS = 10
YOUTUBE_LOOKBACK_DAYS = 90
STALENESS_HOURS = 30

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
}

LOGO_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M12 1.5 22 7v10l-10 5.5L2 17V7L12 1.5Z" stroke="url(#lg)" stroke-width="1.3"/>'
    '<circle cx="12" cy="12" r="3.1" fill="var(--cyan)"/>'
    '<defs><linearGradient id="lg" x1="2" y1="1.5" x2="22" y2="22.5">'
    '<stop stop-color="var(--violet)"/><stop offset="1" stop-color="var(--cyan)"/>'
    '</linearGradient></defs></svg>'
)


def unverified_brands():
    return [bid for bid, b in BRANDS.items() if not b.get("verified")]


def client_brand_id():
    for bid, b in BRANDS.items():
        if b.get("is_client"):
            return bid
    raise RuntimeError("no brand flagged is_client in config.py")
