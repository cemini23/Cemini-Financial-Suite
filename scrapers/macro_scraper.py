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

            # 2. Fear & Greed Index — CNN production endpoint (public, no key required)
            try:
                fgi_resp = requests.get(
                    "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                    timeout=8,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                fgi_resp.raise_for_status()
                new_fgi = float(fgi_resp.json()["fear_and_greed"]["score"])
                r.set("macro:fear_greed", new_fgi)
                print(f"⚖️ Fear & Greed: {new_fgi:.1f}")
            except Exception as fgi_err:
                print(f"API_FAIL: CNN Fear & Greed fetch failed ({fgi_err}), keeping existing value")

        except Exception as e:
            print(f"⚠️ Macro Error: {e}")

        time.sleep(300) # Every 5 mins

if __name__ == "__main__":
    main()
