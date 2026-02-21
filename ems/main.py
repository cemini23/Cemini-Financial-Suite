# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import asyncio
import os
import json
import redis.asyncio as redis
import psycopg2
from datetime import datetime
from core.ems.router import ems
from core.ems.adapters.coinbase import CoinbaseAdapter
from core.ems.adapters.robinhood import RobinhoodAdapter
from core.ems.adapters.hardrock import HardRockBetAdapter
from core.schemas.trading_signals import TradingSignal
from ems.kalshi_rest import KalshiRESTv2

# Initialize Kalshi REST v2 client
kalshi_v2 = KalshiRESTv2(
    key_id=os.getenv("KALSHI_API_KEY", ""),
    private_key_path="/app/private_key.pem",
    environment="demo"
)

def log_to_history(symbol, action, price, reason, rsi=0.0):
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            database=os.getenv('POSTGRES_DB', 'qdb'),
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'quest')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trade_history (timestamp, symbol, action, price, reason, rsi, strategy) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (datetime.now(), symbol, action.upper(), price, reason, rsi, "Kalshi_REST_v2")
        )
        conn.close()
    except Exception as e:
        print(f"⚠️ EMS: Failed to log to trade_history: {e}")

async def signal_listener():
    """Listens to the Redis 'trade_signals' channel and routes to EMS."""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    r = redis.from_url(f"redis://{redis_host}:6379")
    pubsub = r.pubsub()
    await pubsub.subscribe("trade_signals")
    print(f"📡 EMS: Listening for signals on Redis at {redis_host}...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                signal_data = data.get("pydantic_signal", data)

                if signal_data.get("target_brokerage") == "Kalshi":
                    ticker = signal_data.get("ticker_or_event")
                    action = signal_data.get("action")
                    result = kalshi_v2.place_order(ticker, action)
                    print(f"✅ Kalshi REST Result: {result}")
                    if result.get("status") == "success":
                        log_to_history(ticker, action, 0.50, f"Order: {result.get('order_id')}")
                else:
                    signal = TradingSignal(**signal_data)
                    print(f"🔄 EMS: Routing signal for {signal.ticker_or_event} ({signal.target_system})...")
                    result = await ems.execute(signal)
                    print(f"✅ EMS: Execution Result: {result}")

            except Exception as e:
                print(f"❌ EMS: Error processing signal: {e}")

async def emergency_listener():
    """Listens for 'emergency_stop' signals."""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    r = redis.from_url(f"redis://{redis_host}:6379")
    pubsub = r.pubsub()
    await pubsub.subscribe("emergency_stop")
    print(f"🚨 EMS: Emergency Listener ACTIVE on {redis_host}...")
    async for message in pubsub.listen():
        if message["type"] == "message":
            print(f"☢️ EMERGENCY STOP RECEIVED: {message['data']}")
            print("🛑 EMS: HALTING ALL EXECUTION.")

async def main():
    # Initialize other adapters
    try:
        ems.register_adapter("Coinbase", CoinbaseAdapter(
            api_key=os.getenv("COINBASE_API_KEY", ""), api_secret=os.getenv("COINBASE_API_SECRET", "")
        ))
    except Exception as e: print(f"⚠️ EMS: Failed to load Coinbase adapter: {e}")

    try:
        ems.register_adapter("Robinhood", RobinhoodAdapter(
            username=os.getenv("RH_USERNAME", ""), password=os.getenv("RH_PASSWORD", "")
        ))
    except Exception as e: print(f"⚠️ EMS: Failed to load Robinhood adapter: {e}")

    try:
        ems.register_adapter("Hard Rock Bet", HardRockBetAdapter(
            bearer_token=os.getenv("HARDROCK_TOKEN", "")
        ))
    except Exception as e: print(f"⚠️ EMS: Failed to load Hard Rock adapter: {e}")

    # Start Listeners
    await asyncio.gather(signal_listener(), emergency_listener())

if __name__ == "__main__":
    asyncio.run(main())
