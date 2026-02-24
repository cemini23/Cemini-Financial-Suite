import yfinance as yf
import redis
import os
import time
import requests
import psycopg2
from datetime import datetime

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
DB_HOST = os.getenv("DB_HOST", "postgres")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")


def main():
    print("📈 Macro Harvester Initialized...")
    r = redis.Redis(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True)

    # Connect to Postgres
    while True:
        try:
            conn = psycopg2.connect(host=DB_HOST, port=5432, user="admin", password="quest", database="qdb")
            conn.autocommit = True
            cursor = conn.cursor()
            break
        except:
            time.sleep(5)

    # 1. Create macro_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macro_logs (
            timestamp TIMESTAMP WITH TIME ZONE,
            fg_index DOUBLE PRECISION,
            yield_10y DOUBLE PRECISION
        );
    """)

    while True:
        try:
            # 1. Pull 10Y Treasury Yield (^TNX)
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="1d")
            yield_10y = 0.0
            if not hist.empty:
                yield_10y = float(hist['Close'].iloc[-1])
                r.set("macro:10y_yield", yield_10y)

            # 2. Fear & Greed Index — alternative.me (free, no key required)
            try:
                fgi_resp = requests.get(
                    "https://api.alternative.me/fng/?limit=1",
                    timeout=8,
                )
                fgi_resp.raise_for_status()
                new_fgi = float(fgi_resp.json()["data"][0]["value"])
                r.set("macro:fear_greed", new_fgi)
            except Exception as fgi_err:
                new_fgi = float(r.get("macro:fear_greed") or 50.0)
                print(f"API_FAIL: Fear & Greed fetch failed ({fgi_err}), keeping existing value {new_fgi:.1f}")

            # 3. Log to Postgres
            cursor.execute(
                "INSERT INTO macro_logs (timestamp, fg_index, yield_10y) VALUES (%s, %s, %s)",
                (datetime.now(), new_fgi, yield_10y)
            )

            print(f"📊 Macro Sync: FGI={new_fgi:.1f} | 10Y={yield_10y:.2f}%")

        except Exception as e:
            print(f"⚠️ Macro Error: {e}")

        time.sleep(300) # Every 5 mins

if __name__ == "__main__":
    main()
