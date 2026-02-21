import psycopg2

def test_ingestion():
    # Connect to QuestDB using the PostgreSQL wire protocol
    # Using localhost since we are running this from the Mac terminal
    conn_str = "postgresql://admin:quest@localhost:8812/qdb"
    try:
        conn = psycopg2.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create the time-series table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_market_ticks (
                symbol SYMBOL,
                price DOUBLE,
                timestamp TIMESTAMP
            ) TIMESTAMP(timestamp) PARTITION BY DAY;
        """)
        
        # Insert a mock Kalshi price tick
        cursor.execute(
            "INSERT INTO raw_market_ticks (symbol, price, timestamp) VALUES (%s, %s, now())",
            ("KXGOLD-24DEC-B2500", 0.45)
        )
        
        print("✅ Data successfully injected into QuestDB!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    test_ingestion()
