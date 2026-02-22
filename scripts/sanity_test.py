import redis
import json
import os

def run_sanity_test():
    """
    Manually injects a $1 signal into Redis to test the full pipeline:
    Brain Bus -> EMS -> Kalshi FIX.
    """
    print("🧪 Starting $1 Execution Sanity Check...")

    # 1. Connect to Redis (Use localhost if running from Mac, 'redis' if in container)
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=6379,
            password=os.getenv('REDIS_PASSWORD', 'cemini_redis_2026'),
            db=0,
            decode_responses=True,
        )

        # 2. Craft a Validated Signal for a Kalshi Market
        # Note: Replace with an active market ID from Kalshi
        test_trade = {
            "verdict": "EXECUTE",
            "symbol": "KXGOLD-24DEC-B2500",
            "action": "buy",
            "position_size": 1.00,
            "confidence_score": 1.0,
            "reasoning": "System Sanity Check - Manual Trigger"
        }

        # 3. Publish to the bus
        print(f"📡 Broadcasting test signal for {test_trade['symbol']}...")
        r.publish('trade_signals', json.dumps(test_trade))

        print("\n✅ SUCCESS: Test signal sent.")
        print("👉 ACTION: Run 'docker logs -f ems' to verify ORDER_PLACED in the FIX stream.")

    except redis.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to Redis. Ensure 'docker-compose up' is running.")

if __name__ == "__main__":
    run_sanity_test()
