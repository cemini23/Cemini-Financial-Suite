import robin_stocks.robinhood as rh
import csv
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from core import ledger

# --- SETUP ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

UserNAME = os.getenv("RH_UserNAME")
PASSWORD = os.getenv("RH_PASSWORD")
LEDGER_FILE = "survivor_ledger.csv"

def login():
    print("🔐 Logging into Robinhood...")
    try:
        rh.login(Username=UserNAME, password=PASSWORD, store_session=True)
    except:
        rh.login(Username=UserNAME, password=PASSWORD)

def sync_ledger():
    print("🔄 Syncing Ledger with Reality...")
    login()
    
    # Initialize ledger to ensure format is correct (adds Quantity column if missing)
    ledger.init_ledger()
    
    # 1. Get Real Positions
    holdings = rh.build_holdings()
    if not holdings:
        print("✅ Portfolio is empty. Nothing to sync.")
        return

    # 2. Get current FIFO positions from Ledger
    current_positions = ledger.get_open_positions()

    # 3. Compare and Add Missing Positions
    new_entries = 0
    for symbol, data in holdings.items():
        rh_qty = float(data['quantity'])
        ledger_qty = current_positions.get(symbol, {}).get('shares_held', 0)
        
        # If there's a significant difference (more than a tiny fractional amount)
        if rh_qty > ledger_qty + 0.000001:
            diff = rh_qty - ledger_qty
            price = float(data['average_buy_price'])
            
            ledger.record_trade("BUY", symbol, price, diff, "Sync (Reality Correction)")
            print(f"📝 Synced {symbol}: Added {diff:.4f} shares to match Robinhood.")
            new_entries += 1
        else:
            print(f"✅ {symbol} is already in sync.")

    print(f"🎉 Sync Complete. Adjusted {new_entries} positions.")

if __name__ == "__main__":
    sync_ledger()
