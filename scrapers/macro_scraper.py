import yfinance as yf
import redis
import os
import time
import random

REDIS_HOST = os.getenv("REDIS_HOST", "redis")

def main():
    print("📈 Macro Scraper Initialized...")
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    
    while True:
        try:
            # 1. Pull 10Y Treasury Yield (^TNX)
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="1d")
            if not hist.empty:
                yield_10y = hist['Close'].iloc[-1]
                r.set("macro:10y_yield", float(yield_10y))
                print(f"📊 10Y Yield Updated: {yield_10y:.2f}%")

            # 2. Mock Fear & Greed Index (Future: Scrape CNN)
            # We will use a random walk for demo, or a fixed value to test logic
            current_fgi = float(r.get("macro:fear_greed") or 50.0)
            new_fgi = max(0, min(100, current_fgi + random.uniform(-5, 5)))
            r.set("macro:fear_greed", new_fgi)
            print(f"⚖️ Fear & Greed: {new_fgi:.1f}")

        except Exception as e:
            print(f"⚠️ Macro Error: {e}")
            
        time.sleep(300) # Every 5 mins

if __name__ == "__main__":
    main()
