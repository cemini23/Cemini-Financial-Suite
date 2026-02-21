# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import asyncio
import json
import os
import websockets
import psycopg2
from datetime import datetime, timezone
from core.config import Credentials

# Polygon.io WebSocket endpoints
POLYGON_WS_URL = os.getenv("POLYGON_WS_URL", "wss://socket.polygon.io/crypto")
POLYGON_API_KEY = Credentials.POLYGON_API_KEY

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = 5432

async def ingest_polygon_ticks():
    """
    High-performance feed handler.
    Streams raw ticks from Polygon.io into Postgres.
    """
    print(f"📡 Ingestion: Connecting to Polygon WebSocket at {POLYGON_WS_URL}...")

    # Connect to Postgres
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=os.getenv("QUESTDB_USER", "admin"),
            password=os.getenv("QUESTDB_PASSWORD", "quest"),
            database="qdb"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print(f"✅ Ingestion: Connected to Postgres at {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"❌ Ingestion: Database connection failure: {e}")
        return

    try:
        async with websockets.connect(POLYGON_WS_URL) as ws:
            # 1. Authentication
            auth_message = {"action": "auth", "params": POLYGON_API_KEY}
            await ws.send(json.dumps(auth_message))

            auth_resp = await ws.recv()
            print(f"✅ Ingestion: Auth Status -> {auth_resp}")

            # 2. Subscription
            # XT.* = All Crypto Trades | T.* = All Stock Trades
            sub_message = {"action": "subscribe", "params": "XT.*"}
            await ws.send(json.dumps(sub_message))
            print("✅ Ingestion: Subscribed to XT.* (All Crypto Trades)")

            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)

                    for event in data:
                        # Process Trade Events (T=Stocks, XT=Crypto)
                        if event.get("ev") in ["T", "XT"]:
                            symbol = event.get("sym") or event.get("pair")
                            price = float(event.get("p", 0))
                            size = float(event.get("s", 0))
                            timestamp_ms = event.get("t")
                            dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

                            cursor.execute(
                                "INSERT INTO raw_market_ticks (symbol, price, volume, timestamp) VALUES (%s, %s, %s, %s)",
                                (symbol, price, size, dt)
                            )

                except websockets.exceptions.ConnectionClosed:
                    print("⚠️ Ingestion: Polygon connection lost. Retrying...")
                    break
                except Exception as e:
                    print(f"❌ Ingestion: Loop error: {e}")
                    continue

    except Exception as e:
        print(f"❌ Ingestion: Connection failure: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(ingest_polygon_ticks())
