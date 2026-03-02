import os
import json
import psycopg2
import redis
from datetime import datetime

# --- CONFIGURATION ---
DB_HOST = os.getenv("DB_HOST", "localhost")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

def main():
    print("🖋️ The Scribe (Logger) Initialized...")

    # 1. Connect to Redis
    r = redis.Redis(host=REDIS_HOST, port=6379, password=os.getenv('REDIS_PASSWORD', 'cemini_redis_2026'), decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe("trade_signals")

    # 2. Connect to Postgres
    conn = psycopg2.connect(
        host=DB_HOST,
        port=5432,
        user=os.getenv("QUESTDB_USER", "admin"),
        password=os.getenv("QUESTDB_PASSWORD", "quest"),
        database="qdb"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # 3. Ensure trade_history table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            timestamp TIMESTAMP WITH TIME ZONE,
            symbol VARCHAR(50),
            action VARCHAR(20),
            price DOUBLE PRECISION,
            reason TEXT,
            rsi DOUBLE PRECISION,
            strategy VARCHAR(100)
        );
    """)
    # Widen reason column if it was created with the old VARCHAR(50) definition
    cursor.execute("""
        ALTER TABLE trade_history
        ALTER COLUMN reason TYPE TEXT;
    """)
    print("✅ Postgres: trade_history table ready.")

    # 4. Listen and echo (EMS is the authoritative writer to trade_history)
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                signal = data.get("pydantic_signal", data)

                symbol = signal.get("ticker_or_event") or data.get("symbol")
                action = (signal.get("action") or data.get("action", "?")).upper()
                price = data.get("price") or 0.0

                print(f"📝 Signal received: {action} {symbol} @ ${price:.2f}")

            except Exception as e:
                print(f"⚠️ Logger Error: {e}")

if __name__ == "__main__":
    main()
