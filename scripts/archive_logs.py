import psycopg2
import pandas as pd
import os
from datetime import datetime

# CEMINI FINANCIAL SUITE™ - Janitor Service
DB_HOST = os.getenv("DB_HOST", "postgres")
ARCHIVE_PATH = "/mnt/archive"

def archive():
    print(f"🧹 Janitor: Starting archive process at {datetime.now()}")
    if not os.path.exists(ARCHIVE_PATH):
        print(f"❌ Error: Archive path {ARCHIVE_PATH} not found.")
        return

    try:
        conn = psycopg2.connect(host=DB_HOST, database='qdb', user='admin', password='quest')
        
        # 1. Archive trade_history
        query = "SELECT * FROM trade_history WHERE timestamp < NOW() - INTERVAL '7 days'"
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trade_history_archive_{date_str}.csv"
            full_path = os.path.join(ARCHIVE_PATH, filename)
            
            df.to_csv(full_path, index=False)
            print(f"✅ Archived {len(df)} records to {full_path}")
            
            # 2. Cleanup (Delete archived records)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trade_history WHERE timestamp < NOW() - INTERVAL '7 days'")
            conn.commit()
            print("🧹 Database cleaned of archived records.")
        else:
            print("ℹ️ No old records found to archive.")
            
        conn.close()
    except Exception as e:
        print(f"❌ Archive Failed: {e}")

if __name__ == "__main__":
    archive()
