import robin_stocks.robinhood as rh
import os
import sys
from dotenv import load_dotenv
from core import tickers  # Imports your list

# SETUP
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

def check_watchlist():
    print(f"📋 Scanning {len(tickers.WATCHLIST)} tickers for errors...")
    
    # Login (Silent Mode)
    try:
        rh.login(Username=os.getenv("RH_UserNAME"), password=os.getenv("RH_PASSWORD"))
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    invalid_tickers = []
    valid_count = 0

    print("-" * 40)
    
    # Fast Check Loop
    for symbol in tickers.WATCHLIST:
        try:
            # We ask Robinhood for the 'Name' of the company.
            # If it returns None, the ticker is fake/delisted.
            quote = rh.get_instruments_by_symbols(symbol)
            
            if quote and quote[0]:
                simple_name = quote[0].get('simple_name') or quote[0].get('name')
                print(f"✅ {symbol.ljust(6)} | {simple_name}")
                valid_count += 1
            else:
                print(f"❌ {symbol.ljust(6)} | NOT FOUND (Typo?)")
                invalid_tickers.append(symbol)
                
        except Exception:
            print(f"❌ {symbol.ljust(6)} | ERROR")
            invalid_tickers.append(symbol)

    print("-" * 40)
    print(f"🏁 SCAN COMPLETE")
    print(f"✅ Valid:   {valid_count}")
    print(f"❌ Invalid: {len(invalid_tickers)}")
    
    if invalid_tickers:
        print("\n⚠️  PLEASE FIX THESE TYPOS IN tickers.py:")
        print(", ".join(invalid_tickers))
    else:
        print("\n🎉 List is 100% Clean. Ready to trade.")

if __name__ == "__main__":
    check_watchlist()