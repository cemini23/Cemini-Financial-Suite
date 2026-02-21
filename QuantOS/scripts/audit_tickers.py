import json
import os

# Check standard JSON config
if os.path.exists('config/tickers.json'):
    try:
        with open('config/tickers.json', 'r') as f:
            data = json.load(f)
            count = len(data.get('active_tickers', []))
            print(f"✅ AUDIT: Found {count} tickers in config/tickers.json")
    except:
        print("⚠️ Could not read config/tickers.json")

# Check Python file if it exists (since you mentioned tickers.py)
if os.path.exists('tickers.py'):
    print("ℹ️ Found a 'tickers.py' file at root.")
if os.path.exists('config/tickers.py'):
    print("ℹ️ Found a 'tickers.py' file in config/.")
if os.path.exists('core/tickers.py'):
    print("ℹ️ Found a 'tickers.py' file in core/.")
