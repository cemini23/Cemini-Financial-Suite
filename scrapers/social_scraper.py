# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import json
import os
import random
import re
import sys
import time
from datetime import datetime

import psycopg2
import praw
import redis

# ── Step 48: Resilience ───────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
try:
    from core.resilience import SyncCircuitBreaker, create_retry_decorator
    from core.resilience_metrics import record_retry, record_circuit_open

    # Reddit circuit breaker — 429s ARE retryable for Reddit (transient rate limits)
    _reddit_cb = SyncCircuitBreaker("social_reddit", fail_max=5, timeout_duration=120.0)
    _reddit_retry = create_retry_decorator(
        "social_reddit", max_attempts=3, base_wait=2.0, max_wait=30.0,
        retryable_statuses=(500, 502, 503, 504),  # 429 excluded for Reddit too (PRAW handles it)
    )

    # X API circuit breaker — 429 must NOT be retried (budget-relevant)
    _x_cb = SyncCircuitBreaker("social_x", fail_max=5, timeout_duration=300.0)
    # X API: empty retryable_statuses = only retry on transport errors, never on HTTP status
    _x_retry = create_retry_decorator(
        "social_x", max_attempts=2, base_wait=5.0, max_wait=30.0,
        retryable_statuses=(),  # 429 is a budget signal — do NOT retry
    )
    _RESILIENCE_AVAILABLE = True
except ImportError:
    _RESILIENCE_AVAILABLE = False
    _reddit_cb = None
    _x_cb = None

try:
    import tweepy
    from textblob import TextBlob
    _X_AVAILABLE = True
except ImportError:
    _X_AVAILABLE = False

# ── ENV CONFIG ────────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
DB_HOST = os.getenv("DB_HOST", "postgres")

X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
X_API_MONTHLY_BUDGET = float(os.getenv("X_API_MONTHLY_BUDGET", "25.00"))
X_API_HARD_SKIP_PCT = float(os.getenv("X_API_HARD_SKIP_PCT", "0.90"))
X_HARD_LIMIT = X_API_MONTHLY_BUDGET * X_API_HARD_SKIP_PCT
X_COST_PER_CALL = 0.03  # estimated $/call on Basic tier

# Tiered polling intervals (seconds)
# Budget math with max_results=10 per OR-query call:
#   Tier 1 (90 min)  → 480 calls/month × 10 reads =  4,800 reads
#   Tier 2 (180 min) → 240 calls/month × 10 reads =  2,400 reads
#   Tier 3 (360 min) → 120 calls/month × 10 reads =  1,200 reads
#   ─────────────────────────────────────────────────────────────
#   Total: 8,400 / 10,000 reads = 84% utilisation ✓
T1_INTERVAL = int(os.getenv("X_TIER1_INTERVAL_MINUTES", "90")) * 60
T2_INTERVAL = int(os.getenv("X_TIER2_INTERVAL_MINUTES", "180")) * 60
T3_INTERVAL = int(os.getenv("X_TIER3_INTERVAL_MINUTES", "360")) * 60
REDDIT_INTERVAL = int(os.getenv("SOCIAL_SCRAPER_INTERVAL_MINUTES", "30")) * 60

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CeminiBot v1.0")
# Set to "true" only in dev/testing — keeps synthetic rows out of RL training data
ENABLE_MOCK_SOCIAL = os.getenv("ENABLE_MOCK_SOCIAL", "false").lower() == "true"

# ── FALLBACK SYMBOLS FOR MOCK MODE ────────────────────────────────────────────
MOCK_SYMBOLS = [
    "SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    "TSLA", "AMD", "PLTR", "COIN",
    "BTC", "ETH", "SOL", "DOGE", "ADA", "AVAX", "LINK",
]

# ── KEYWORD ROUTERS ───────────────────────────────────────────────────────────
WEATHER_KW = frozenset({
    "weather", "storm", "temperature", "forecast", "hurricane", "tropical",
    "tornado", "flood", "drought", "heatwave", "blizzard", "frost",
    "precip", "rainfall", "snowfall", "wind", "advisory", "warning",
    "watches", "issued", "degrees", "nws", "noaa",
})

GEO_KW = frozenset({
    "war", "invasion", "missile", "election", "strike", "conflict",
    "military", "emergency", "breaking", "alert", "crisis", "sanctions",
    "border", "ceasefire", "escalation", "troops", "attack",
})


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _load_account_tiers():
    config_path = os.path.join(os.path.dirname(__file__), "x_accounts.json")
    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load x_accounts.json: {e}")
        return {}


def _get_x_spend(r):
    try:
        return float(r.get("x_api:monthly_spend") or 0.0)
    except Exception:
        return 0.0


def _incr_x_spend(r, amount=X_COST_PER_CALL):
    current = _get_x_spend(r)
    new_val = round(current + amount, 4)
    try:
        r.set("x_api:monthly_spend", str(new_val))
    except Exception:
        pass
    return new_val


def _publish_intel(r, key, payload, ttl=300):
    """Write a value to the intel bus (Redis key with TTL)."""
    try:
        r.set(key, json.dumps(payload), ex=ttl)
    except Exception:
        pass


# ── X API TIER POLL ───────────────────────────────────────────────────────────

def poll_x_tier(tier_num, tier_cfg, x_client, r, cursor):
    """
    Fires one OR-query batch for the given tier.
    Scores tweets with TextBlob, writes to sentiment_logs, routes to intel bus.
    """
    accounts = tier_cfg.get("accounts", [])
    route_key = tier_cfg.get("route", "")
    if not accounts or not x_client:
        return

    x_spend = _get_x_spend(r)
    if x_spend >= X_HARD_LIMIT:
        print(
            f"[BUDGET HALT] Tier {tier_num}: spend ${x_spend:.2f} >= "
            f"hard limit ${X_HARD_LIMIT:.2f}. Skipping poll."
        )
        return

    # Build a single OR query — cap at 20 handles to stay under the 512-char limit
    handles = [a.lstrip('@') for a in accounts[:20]]
    query = "(" + " OR ".join(f"from:{h}" for h in handles) + ") -is:retweet lang:en"

    try:
        response = x_client.search_recent_tweets(
            query=query,
            max_results=10,
            tweet_fields=["author_id", "text", "created_at"],
            expansions=["author_id"],
            user_fields=["username"],
        )
    except Exception as e:
        print(f"⚠️  X API Tier {tier_num} query failed: {e}")
        return

    tweets = response.data or []

    # Build author_id → username map from the expansions sidecar
    user_map = {}
    if response.includes and response.includes.get("users"):
        for u in response.includes["users"]:
            user_map[str(u.id)] = u.username

    timestamp = datetime.now()
    polarity_sum = 0.0
    scored = []

    for tweet in tweets:
        text = tweet.text
        text_lower = text.lower()
        author = user_map.get(str(tweet.author_id), str(tweet.author_id))

        try:
            polarity = TextBlob(text).sentiment.polarity
        except Exception:
            polarity = 0.0

        polarity_sum += polarity
        scored.append({
            "author": author,
            "polarity": polarity,
            "text": text,
            "lower": text_lower,
        })

        # Persist to sentiment_logs
        try:
            cursor.execute(
                "INSERT INTO sentiment_logs (timestamp, symbol, sentiment_score, source)"
                " VALUES (%s, %s, %s, %s)",
                (timestamp, author[:50], round(polarity, 4), f"x_tier{tier_num}"),
            )
        except Exception:
            pass

    n = len(scored)
    avg_polarity = polarity_sum / n if n else 0.0

    # ── Route to intel bus ────────────────────────────────────────────────────
    if tier_num == 1:
        # Finance → intel:social_score (SocialAnalyzer reads this)
        _publish_intel(r, "intel:social_score", {
            "value": {"score": round(avg_polarity, 4), "top_ticker": "MARKET"},
            "source_system": "SocialScraper/T1",
            "timestamp": time.time(),
            "confidence": min(1.0, n / 10.0),
        })

    elif tier_num == 2:
        # Weather / Macro — find first weather-keyword tweet and surface it
        for s in scored:
            if any(kw in s["lower"] for kw in WEATHER_KW):
                _publish_intel(r, "intel:weather_tweet", {
                    "account": s["author"],
                    "text": s["text"][:200],
                    "polarity": s["polarity"],
                    "ts": timestamp.isoformat(),
                }, ttl=3600)
                break

    elif tier_num == 3:
        # News / Geo — surface first geo-keyword tweet
        for s in scored:
            if any(kw in s["lower"] for kw in GEO_KW):
                impact = "HIGH" if abs(s["polarity"]) > 0.5 else "MODERATE"
                _publish_intel(r, "intel:geo_news", {
                    "account": s["author"],
                    "text": s["text"][:200],
                    "impact": impact,
                    "ts": timestamp.isoformat(),
                }, ttl=7200)
                break

    new_spend = _incr_x_spend(r)
    print(
        f"SOCIAL_SCRAPER: [TIER {tier_num}] polled {n} tweets"
        f" from {len(accounts)} accounts"
        f" | API spend: ${new_spend:.2f} / ${X_API_MONTHLY_BUDGET:.2f}"
    )


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("🤖 Social Scraper (Heatseeker Edition) Initialized...")

    r = redis.Redis(
        host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True
    )

    conn = psycopg2.connect(
        host=DB_HOST, port=5432,
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "quest"),
        database=os.getenv("POSTGRES_DB", "qdb"),
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_logs (
            timestamp TIMESTAMP WITH TIME ZONE,
            symbol VARCHAR(50),
            sentiment_score DOUBLE PRECISION,
            source VARCHAR(50)
        );
    """)

    # ── Reddit setup ──────────────────────────────────────────────────────────
    reddit = None
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        try:
            reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT,
            )
        except Exception:
            reddit = None

    # ── X API setup ───────────────────────────────────────────────────────────
    x_client = None
    if _X_AVAILABLE and X_BEARER_TOKEN:
        try:
            x_client = tweepy.Client(bearer_token=X_BEARER_TOKEN, wait_on_rate_limit=True)
            print("✅ X API client initialised.")
        except Exception as e:
            print(f"⚠️  X API init failed: {e}")
    else:
        print("ℹ️  X API disabled (X_BEARER_TOKEN not set or tweepy not installed).")

    # ── Load account tiers ────────────────────────────────────────────────────
    tiers = _load_account_tiers()
    tier1_cfg = tiers.get("tier1_finance", {})
    tier2_cfg = tiers.get("tier2_weather_macro", {})
    tier3_cfg = tiers.get("tier3_news", {})

    t1_n = len(tier1_cfg.get("accounts", []))
    t2_n = len(tier2_cfg.get("accounts", []))
    t3_n = len(tier3_cfg.get("accounts", []))
    t1_m = T1_INTERVAL // 60
    t2_m = T2_INTERVAL // 60
    t3_m = T3_INTERVAL // 60

    # Budget projection
    t1_reads = int(30 * 24 * 60 / t1_m * 10)
    t2_reads = int(30 * 24 * 60 / t2_m * 10)
    t3_reads = int(30 * 24 * 60 / t3_m * 10)
    total_reads = t1_reads + t2_reads + t3_reads

    print(
        f"📋 Tiers: T1={t1_n} accts/{t1_m}min"
        f" | T2={t2_n} accts/{t2_m}min"
        f" | T3={t3_n} accts/{t3_m}min"
    )
    print(
        f"📊 Budget projection: ~{total_reads:,} reads/month"
        f" vs 10,000 limit"
        f" | Hard stop at ${X_HARD_LIMIT:.2f} / ${X_API_MONTHLY_BUDGET:.2f}"
    )
    print(
        f"⏱️  Reddit: every {REDDIT_INTERVAL // 60}min"
        f" | X tiers: {t1_m}/{t2_m}/{t3_m}min"
    )

    # ── Independent tier timers ───────────────────────────────────────────────
    last_poll = {"reddit": 0.0, "t1": 0.0, "t2": 0.0, "t3": 0.0}

    # ── Main loop — tick every 30s to check which tier is due ─────────────────
    while True:
        now = time.time()

        # Reddit / mock poll
        if now - last_poll["reddit"] >= REDDIT_INTERVAL:
            try:
                timestamp = datetime.now()
                if reddit:
                    for submission in reddit.subreddit("wallstreetbets").hot(limit=25):
                        tickers = re.findall(r'\b[A-Z]{3,5}\b', submission.title)
                        for t in tickers:
                            score = (
                                0.5 if "call" in submission.title.lower()
                                else -0.5 if "put" in submission.title.lower()
                                else 0.1
                            )
                            cursor.execute(
                                "INSERT INTO sentiment_logs"
                                " (timestamp, symbol, sentiment_score, source)"
                                " VALUES (%s, %s, %s, %s)",
                                (timestamp, t, score, "reddit"),
                            )
                else:
                    if ENABLE_MOCK_SOCIAL:
                        for sym in MOCK_SYMBOLS:
                            cursor.execute(
                                "INSERT INTO sentiment_logs"
                                " (timestamp, symbol, sentiment_score, source)"
                                " VALUES (%s, %s, %s, %s)",
                                (timestamp, sym, round(random.uniform(-0.2, 0.8), 2), "mock_social"),
                            )
                    else:
                        print("SOCIAL_SCRAPER: mock_social disabled (ENABLE_MOCK_SOCIAL=false) — no synthetic inserts")
                x_spend = _get_x_spend(r)
                src = "reddit" if reddit else "mock"
                print(
                    f"SOCIAL_SCRAPER: [{src}] cycle complete"
                    f" | X API spend: ${x_spend:.2f} / ${X_API_MONTHLY_BUDGET:.2f}"
                    f" | next in {REDDIT_INTERVAL // 60}m"
                )
            except Exception as e:
                print(f"⚠️  Reddit/mock error: {e}")
            last_poll["reddit"] = now

        # X API tier polls (only if client is available)
        if x_client:
            if now - last_poll["t1"] >= T1_INTERVAL:
                if _RESILIENCE_AVAILABLE and _x_cb is not None:
                    _x_cb.call(poll_x_tier, 1, tier1_cfg, x_client, r, cursor)
                else:
                    poll_x_tier(1, tier1_cfg, x_client, r, cursor)
                last_poll["t1"] = now

            if now - last_poll["t2"] >= T2_INTERVAL:
                if _RESILIENCE_AVAILABLE and _x_cb is not None:
                    _x_cb.call(poll_x_tier, 2, tier2_cfg, x_client, r, cursor)
                else:
                    poll_x_tier(2, tier2_cfg, x_client, r, cursor)
                last_poll["t2"] = now

            if now - last_poll["t3"] >= T3_INTERVAL:
                if _RESILIENCE_AVAILABLE and _x_cb is not None:
                    _x_cb.call(poll_x_tier, 3, tier3_cfg, x_client, r, cursor)
                else:
                    poll_x_tier(3, tier3_cfg, x_client, r, cursor)
                last_poll["t3"] = now

        time.sleep(30)  # tick every 30 s — fine-grained enough for any interval above


if __name__ == "__main__":
    main()
