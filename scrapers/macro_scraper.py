import yfinance as yf
import redis
import os
import time
import requests

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")


def main():
    print("📈 Macro Scraper Initialized...")
    r = redis.Redis(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True)

    while True:
        try:
            # 1. Pull 10Y Treasury Yield (^TNX)
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="1d")
            if not hist.empty:
                yield_10y = hist['Close'].iloc[-1]
                r.set("macro:10y_yield", float(yield_10y))
                print(f"📊 10Y Yield Updated: {yield_10y:.2f}%")

            # 2. Fear & Greed Index — alternative.me (free, no key required)
            try:
                fgi_resp = requests.get(
                    "https://api.alternative.me/fng/?limit=1",
                    timeout=8,
                )
                fgi_resp.raise_for_status()
                new_fgi = float(fgi_resp.json()["data"][0]["value"])
                r.set("macro:fear_greed", new_fgi)
                print(f"⚖️ Fear & Greed: {new_fgi:.1f}")
            except Exception as fgi_err:
                print(f"API_FAIL: Fear & Greed fetch failed ({fgi_err}), keeping existing value")

        except Exception as e:
            print(f"⚠️ Macro Error: {e}")

        time.sleep(300) # Every 5 mins

if __name__ == "__main__":
    main()
