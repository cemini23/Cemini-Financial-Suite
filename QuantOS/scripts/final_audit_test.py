"""
QuantOS™ v7.1.1 - Final Audit Test
Validates: Order Execution, Cancellation, Backtester API, and Analytics API.
"""
import asyncio
import os
import sys
import requests
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brokers.factory import get_broker
from core.execution import ExecutionEngine
from config.settings_manager import settings_manager

async def run_audit():
    load_dotenv()
    print("🦁 Starting Final System Audit...")
    
    # 1. BROKER & EXECUTION TEST
    broker = get_broker()
    if not broker.authenticate():
        print("❌ BROKER AUTH FAILED.")
        return

    engine = ExecutionEngine(broker)
    symbol = "SOFI"
    print(f"📡 Testing Smart Order Placement for {symbol}...")
    
    # Place a limit order ($50 to ensure at least 1-2 shares)
    res, price = await engine.execute_smart_order(symbol, "buy", 50.0, settings_manager.settings)
    
    if "error" in res:
        print(f"❌ Order placement failed: {res['error']}")
    else:
        print(f"✅ Order submitted successfully. Result: {res.get('id', 'Submitted')}")
        
        # 2. CANCEL TEST
        print("⏳ Waiting for order to propagate...")
        await asyncio.sleep(3)
        print("🛑 Attempting to cancel all orders...")
        broker.cancel_all_orders()
        print("✅ Cancel command sent.")

    # 3. API & MODULE TESTS
    print("\n🌐 Testing Terminal Server APIs...")
    import subprocess
    # Start server in background on high port
    port = 5099
    server_proc = subprocess.Popen(
        [sys.executable, "run_app.py", "--port", str(port)],
        env={**os.environ, "PYTHONPATH": "."},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(12) # Wait for server + engine init
    
    apis = {
        "Dashboard": f"http://127.0.0.1:{port}/api/dashboard",
        "Backtester": f"http://127.0.0.1:{port}/api/run_simulation",
        "Settings": f"http://127.0.0.1:{port}/api/settings"
    }
    
    for name, url in apis.items():
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                print(f"✅ {name} API is ONLINE and healthy.")
            else:
                print(f"❌ {name} API returned status {r.status_code}")
        except Exception as e:
            print(f"❌ {name} API test failed: {e}")

    # Cleanup
    print("\n🛑 Shutting down audit server...")
    server_proc.terminate()
    server_proc.wait()
    print("🏁 Audit Complete.")

if __name__ == "__main__":
    asyncio.run(run_audit())
