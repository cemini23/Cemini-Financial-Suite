import praw
import redis
import os
import time
import json
import re
import psycopg2
from datetime import datetime

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
DB_HOST = os.getenv("DB_HOST", "postgres")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")

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

    while True:
        try:
            timestamp = datetime.now()
            if reddit:
                for submission in reddit.subreddit("wallstreetbets").hot(limit=25):
                    tickers = re.findall(r'\b[A-Z]{3,5}\b', submission.title)
                    for t in tickers:
                        # Simple dummy sentiment for now, can integrate TextBlob later
                        score = 0.5 if "call" in submission.title.lower() else -0.5 if "put" in submission.title.lower() else 0.1
                        cursor.execute("INSERT INTO sentiment_logs (timestamp, symbol, sentiment_score, source) VALUES (%s, %s, %s, %s)",
                                       (timestamp, t, score, "reddit"))
            else:
                # Mock high-density spikes for testing if no API keys
                mock_tickers = ["BTC", "NVDA", "TSLA", "GME", "AMD"]
                for t in mock_tickers:
                    # Occasional spike simulation
                    count = 20 if t == "BTC" and time.time() % 60 < 10 else 2
                    for _ in range(count):
                        cursor.execute("INSERT INTO sentiment_logs (timestamp, symbol, sentiment_score, source) VALUES (%s, %s, %s, %s)",
                                       (timestamp, t, 0.2, "mock_social"))
                print("📝 Generated Mock Sentiment Ticks.")

            time.sleep(60) # Scan more frequently for Heatseeker density

        except Exception as e:
            print(f"⚠️ Social Scraper Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
