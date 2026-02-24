# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import os
import time
import requests
import psycopg2
from datetime import datetime, timezone, timedelta, time as dt_time
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = 5432

# Crypto tickers use X: prefix on Polygon REST API
CRYPTO_SYMBOLS = [
    "X:BTCUSD", "X:ETHUSD", "X:SOLUSD",
    "X:DOGEUSD", "X:ADAUSD", "X:AVAXUSD", "X:LINKUSD",
]

# Stock tickers — only available during market hours (9:30–16:00 ET)
STOCK_SYMBOLS = [
    "SPY", "QQQ", "IWM",
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    "TSLA", "AMD", "SMCI", "PLTR", "AVGO",
    "COIN", "MSTR", "MARA",
    "JPM", "BAC", "GS",
    "DIS", "NFLX", "UBER",
]

# Polygon free tier: 5 calls/minute → sleep 13s between calls to stay safe
RATE_LIMIT_SLEEP = 13
POLL_INTERVAL = 60  # seconds between full cycles


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=os.getenv("QUESTDB_USER", "admin"),
        password=os.getenv("QUESTDB_PASSWORD", "quest"),
        database="qdb"
    )


def ensure_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_market_ticks (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)


def fetch_and_insert(cursor, ticker, display_symbol, from_dt, to_dt):
    """Fetch 1-minute bars from Polygon REST API and insert into DB."""
    from_str = from_dt.strftime("%Y-%m-%d")
    to_str = to_dt.strftime("%Y-%m-%d")
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}"
        f"/range/1/minute/{from_str}/{to_str}"
        f"?adjusted=true&sort=desc&limit=5&apiKey={POLYGON_API_KEY}"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return

        latest = results[0]
        price = float(latest.get("c", 0))   # close price
        volume = float(latest.get("v", 0))
        ts_ms = latest.get("t", 0)
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)

        cursor.execute(
            "INSERT INTO raw_market_ticks (symbol, price, volume, timestamp) "
            "VALUES (%s, %s, %s, %s)",
            (display_symbol, price, volume, dt)
        )
        n = len(results)
        print(
            f"POLYGON_REST: Fetched {n} ticks for {display_symbol}, "
            f"latest price: ${price:.4f}"
        )
    except requests.HTTPError as e:
        print(f"WARNING: Polygon HTTP error for {display_symbol}: {e} — skipping")
    except Exception as e:
        print(f"WARNING: Error fetching {display_symbol}: {e} — skipping")


def _is_market_hours():
    """True if US equity markets are open (Mon-Fri 9:30-16:00 ET)."""
    now_et = datetime.now(tz=_ET)
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return dt_time(9, 30) <= now_et.time() <= dt_time(16, 0)


def run_poll_cycle(cursor, conn):
    now = datetime.now(tz=timezone.utc)
    yesterday = now - timedelta(days=1)

    # Crypto: always poll (24/7 markets)
    crypto_pairs = [
        (ticker, ticker.replace("X:", "").replace("USD", "-USD"))
        for ticker in CRYPTO_SYMBOLS
    ]
    for ticker, display in crypto_pairs:
        fetch_and_insert(cursor, ticker, display, yesterday, now)
        time.sleep(RATE_LIMIT_SLEEP)

    # Stocks: only during market hours to avoid empty-result calls
    if _is_market_hours():
        for ticker in STOCK_SYMBOLS:
            fetch_and_insert(cursor, ticker, ticker, yesterday, now)
            time.sleep(RATE_LIMIT_SLEEP)
    else:
        print("POLYGON_REST: Market closed — skipping stock symbols this cycle")


def main():
    print("POLYGON_REST: Ingestor starting (REST polling mode)...")

    conn = None
    while conn is None:
        try:
            conn = get_db_connection()
            conn.autocommit = True
            print(f"POLYGON_REST: Connected to Postgres at {DB_HOST}:{DB_PORT}")
        except Exception as e:
            print(f"WARNING: DB connection failed: {e} — retrying in 5s")
            time.sleep(5)

    cursor = conn.cursor()
    ensure_table(cursor)
    print("POLYGON_REST: raw_market_ticks table ready.")

    while True:
        try:
            print("POLYGON_REST: Starting poll cycle...")
            run_poll_cycle(cursor, conn)
            print(f"POLYGON_REST: Cycle complete. Sleeping {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)
        except psycopg2.InterfaceError:
            print("WARNING: DB connection lost — reconnecting...")
            try:
                conn = get_db_connection()
                conn.autocommit = True
                cursor = conn.cursor()
            except Exception as e:
                print(f"WARNING: Reconnect failed: {e}")
                time.sleep(10)
        except Exception as e:
            print(f"WARNING: Poll cycle error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
