"""
QuantOS™ v12.0.0 - Universal Watchlist Loader
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import json
import os

# Base directory for relative pathing
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKER_CONFIG_PATH = os.path.join(BASE_DIR, "config", "tickers.json")

def load_watchlist():
    """Loads the active ticker list from config/tickers.json."""
    try:
        if os.path.exists(TICKER_CONFIG_PATH):
            with open(TICKER_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get("active_tickers", [])
    except Exception as e:
        print(f"⚠️  HARVESTER: Failed to load tickers.json: {e}")
    
    # Static fallback for critical system safety
    return ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "BTC-USD"]

# Global constants for engine-wide access
WATCHLIST = load_watchlist()

def get_categories():
    """Returns the full category dictionary from the config file."""
    try:
        if os.path.exists(TICKER_CONFIG_PATH):
            with open(TICKER_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get("categories", {})
    except Exception:
        pass
    return {}
