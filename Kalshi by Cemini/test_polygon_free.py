import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_free_tier():
    api_key = os.getenv("POLYGON_API_KEY")
    
    # Calculate yesterday's date (Free tier requires past data)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    ticker = "SPY" # A standard stock ticker
    
    # The endpoint for daily aggregates
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{yesterday}/{yesterday}?apiKey={api_key}"
    
    print(f"📡 Requesting free EOD data for {ticker} on {yesterday}...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if "results" in data:
            close_price = data['results'][0]['c']
            print(f"✅ SUCCESS! {ticker} closed at ${close_price}")
        else:
            print(f"⚠️ API connected, but no market data for that specific day (Market might have been closed).")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_free_tier()
