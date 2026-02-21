# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import os
import json
from ems.kalshi_rest import KalshiRESTv2
from dotenv import load_dotenv

load_dotenv()

def ping_kalshi():
    print("📡 KALSHI REST v2: PING TEST")
    key_id = os.getenv("KALSHI_API_KEY")
    # Path inside project since we run from root
    private_key_path = "Kalshi by Cemini/private_key.pem"
    
    if not key_id:
        print("❌ Missing KALSHI_API_KEY in .env")
        return

    client = KalshiRESTv2(
        key_id=key_id,
        private_key_path=private_key_path,
        environment="demo"
    )
    
    # Try to fetch balance as a ping
    path = "/portfolio/balance"
    headers = client._get_headers("GET", path)
    
    import requests
    try:
        resp = requests.get(client.base_url + path, headers=headers)
        if resp.status_code == 200:
            print(f"✅ Connection Successful! Balance: ${resp.json().get('balance', 0)/100:.2f}")
        else:
            print(f"❌ Connection Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ping_kalshi()
