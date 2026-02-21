import yfinance as yf
import psycopg2
import time
import os

def connect_to_db():
    db_host = os.getenv("DB_HOST", "postgres")
    conn_str = f"postgresql://admin:quest@{db_host}:5432/qdb"
    try:
        conn = psycopg2.connect(conn_str)
        conn.autocommit = True 
        return conn
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")
        return None

def get_live_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # Pull the absolute latest 1-minute candle
        todays_data = ticker.history(period='1d', interval='1m')
        if not todays_data.empty:
            return todays_data['Close'].iloc[-1]
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")
    return None

def main():
    print("👀 yfinance Ingestor Starting... pulling live free data.")
    
    conn = None
    while not conn:
        conn = connect_to_db()
        if not conn:
            print("⏳ Database not ready. Retrying in 5s...")
            time.sleep(5)
            
    cursor = conn.cursor()
    
    # Ensure our table exists (Universal Postgres Syntax)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_market_ticks (
            symbol VARCHAR(50),
            price DOUBLE PRECISION,
            timestamp TIMESTAMP WITH TIME ZONE
        );
    """)

    # Symbols you want to track (e.g., tracking the S&P 500 for Kalshi markets)
    symbols_to_track = ["SPY", "QQQ"] 

    while True:
        for symbol in symbols_to_track:
            price = get_live_price(symbol)
            if price:
                cursor.execute(
                    "INSERT INTO raw_market_ticks (symbol, price, timestamp) VALUES (%s, %s, now())",
                    (symbol, float(price))
                )
                print(f"✅ TICK: {symbol} @ ${price:.2f}")
        
        # Pause to avoid getting rate-limited by Yahoo
        time.sleep(5) 

if __name__ == "__main__":
    main()
