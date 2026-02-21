import json
import os
import sys

# Add project root to path to import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tickers import WATCHLIST

TICKERS_FILE = 'config/tickers.json'

NEW_TICKERS = [
    "NVDA", "TSLA", "AMD",   # High Volatility Tech
    "MSTR", "COIN", "BITO",  # Crypto Proxies
    "XLF", "TLT"             # Sector & Rates
]

def add_tickers():
    # Combine original WATCHLIST from core/tickers.py with the expansion pack
    full_list = list(set(WATCHLIST + NEW_TICKERS))
    full_list.sort() # Keep it clean
    
    data = {"active_tickers": full_list}
    
    # Ensure config directory exists
    os.makedirs(os.path.dirname(TICKERS_FILE), exist_ok=True)
    
    with open(TICKERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Portfolio expanded. Now tracking {len(full_list)} assets.")

if __name__ == "__main__":
    add_tickers()

if __name__ == "__main__":
    add_tickers()
