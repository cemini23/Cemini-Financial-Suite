import os
import sys
import json

# Force Absolute Project Root
PROJECT_ROOT = "/Users/claudiobarone/Desktop/QuantOS"
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from interface import create_app

def verify():
    print("🔍 FINAL GOLDEN MASTER VERIFICATION...")
    print(f"📍 Project Root: {PROJECT_ROOT}")
    print(f"📍 CWD: {os.getcwd()}")
    
    errors = []
    
    # 1. Check Assets
    logo_path = os.path.join(PROJECT_ROOT, "interface", "static", "quantos_v9_emblem.png")
    if not os.path.exists(logo_path):
        errors.append(f"Logo missing at: {logo_path}")
    else:
        print("✅ Logo Asset: FOUND")

    # 2. Check Config
    ticker_path = os.path.join(PROJECT_ROOT, "config", "tickers.json")
    try:
        with open(ticker_path, 'r') as f:
            if "NVDA" in f.read():
                print("✅ Ticker Logic: NVDA PRESENT")
    except Exception as e:
        errors.append(f"Tickers error: {e}")

    # 3. Check Server (Explicitly creating a new app instance for testing)
    try:
        app = create_app()
        client = TestClient(app)
        
        # We test a simple route first
        health = client.get("/health")
        if health.status_code == 200:
            print("✅ API Health: ONLINE")
        else:
            errors.append(f"Health check failed: {health.status_code}")

        # The Static Test
        static_file = client.get("/static/quantos_v9_emblem.png")
        if static_file.status_code == 200:
            print("✅ Static Mount: VERIFIED")
        else:
            errors.append(f"Static file unreachable (404)")

        # The Template Test (This usually triggers the url_for error)
        dashboard = client.get("/")
        if dashboard.status_code == 200:
            print("✅ Dashboard Render: SUCCESS")
        else:
            # If it fails here, the NoMatchFound error is usually in the traceback
            errors.append(f"Dashboard render failed ({dashboard.status_code})")

    except Exception as e:
        errors.append(f"Verification Exception: {e}")

    if errors:
        print("\n❌ VERIFICATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✅ SYSTEM GREEN. READY FOR ZIP.")

if __name__ == "__main__":
    verify()
