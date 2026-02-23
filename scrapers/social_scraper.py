import praw
import redis
import os
import time
import json
import re
import random
import psycopg2
from datetime import datetime

MOCK_SYMBOLS = [
    "SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    "TSLA", "AMD", "PLTR", "COIN",
    "BTC", "ETH", "SOL", "DOGE", "ADA", "AVAX", "LINK",
]

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
DB_HOST = os.getenv("DB_HOST", "postgres")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")

# Budget / interval config — override via .env
X_API_MONTHLY_BUDGET = float(os.getenv("X_API_MONTHLY_BUDGET", "25.00"))
INTERVAL_MINUTES = int(os.getenv("SOCIAL_SCRAPER_INTERVAL_MINUTES", "30"))
INTERVAL_SECONDS = INTERVAL_MINUTES * 60

# Credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CeminiBot v1.0")


def main():
    print("🤖 Social Scraper (Heatseeker Edition) Initialized...")
    r = redis.Redis(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True)

    # Connect to Postgres
    conn = psycopg2.connect(host=DB_HOST, port=5432, user="admin", password="quest", database="qdb")
    conn.autocommit = True
    cursor = conn.cursor()

    # 1. Ensure sentiment_logs table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_logs (
            timestamp TIMESTAMP WITH TIME ZONE,
            symbol VARCHAR(50),
            sentiment_score DOUBLE PRECISION,
            source VARCHAR(50)
        );
    """)

    # Reddit Setup
    has_creds = REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
    reddit = None
    if has_creds:
        try:
            reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent=REDDIT_USER_AGENT)
        except Exception: reddit = None

    print(f"⏱️  Social Scraper interval: {INTERVAL_MINUTES}m | X API budget: ${X_API_MONTHLY_BUDGET:.2f}")

    while True:
        try:
            timestamp = datetime.now()
            if reddit:
                for submission in reddit.subreddit("wallstreetbets").hot(limit=25):
                    tickers = re.findall(r'\b[A-Z]{3,5}\b', submission.title)
                    for t in tickers:
                        score = 0.5 if "call" in submission.title.lower() else -0.5 if "put" in submission.title.lower() else 0.1
                        cursor.execute(
                            "INSERT INTO sentiment_logs (timestamp, symbol, sentiment_score, source)"
                            " VALUES (%s, %s, %s, %s)",
                            (timestamp, t, score, "reddit"),
                        )
            else:
                # No Reddit creds — write mock sentiment so downstream has data
                for sym in MOCK_SYMBOLS:
                    score = round(random.uniform(-0.2, 0.8), 2)
                    cursor.execute(
                        "INSERT INTO sentiment_logs"
                        " (timestamp, symbol, sentiment_score, source)"
                        " VALUES (%s, %s, %s, %s)",
                        (timestamp, sym, score, "mock_social"),
                    )

            # Read X API spend from Redis (written by Kalshi SocialAnalyzer)
            try:
                x_spend = float(r.get("x_api:monthly_spend") or 0.0)
            except Exception:
                x_spend = 0.0

            print(
                f"SOCIAL_SCRAPER: cycle complete, X API spend: "
                f"${x_spend:.2f} / ${X_API_MONTHLY_BUDGET:.2f} | "
                f"next scan in {INTERVAL_MINUTES}m"
            )
            time.sleep(INTERVAL_SECONDS)

        except Exception as e:
            print(f"⚠️ Social Scraper Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
