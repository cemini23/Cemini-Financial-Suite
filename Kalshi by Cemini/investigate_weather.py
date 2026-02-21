from app.core.database import SessionLocal
# Assuming SignalLog model exists or we query raw
from sqlalchemy import text
import pandas as pd

def investigate():
    db = SessionLocal()
    print("🔎 INVESTIGATING WEATHER MODULE HISTORY...\n")

    try:
        # Use raw SQL to be safe if model names differ
        query = text("SELECT timestamp, signal, confidence, outcome FROM signal_logs WHERE module = 'Weather Alpha' ORDER BY timestamp DESC LIMIT 10")
        result = db.execute(query).fetchall()

        if not result:
            print("❌ No Weather trades found in database.")
            return

        print(f"{'TIMESTAMP':<20} | {'SIGNAL':<15} | {'CONFIDENCE':<10} | {'OUTCOME'}")
        print("-" * 60)

        for row in result:
            print(f"{str(row[0]):<20} | {row[1]:<15} | {row[2]:<10} | {row[3]}")

        print("\n💡 ANALYSIS:")
        print("If you see 'CONFIDENCE' dropping rapidly (e.g., 85 -> 20), the models (NWS/Euro) likely diverged suddenly.")
        print("If 'OUTCOME' is empty, the trade was identified but never executed (Allocator rejected it).")
    except Exception as e:
        print(f"⚠️ Query Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    investigate()
