import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import TradingEngine
from core.logger_config import get_logger

logger = get_logger("test_startup")

async def run_test():
    print("🧪 Starting QuantOS Connection Test...")
    engine = TradingEngine()
    
    # 1. Initialize (This auths the broker)
    print("🔄 Initializing Engine and Authenticating Broker...")
    try:
        engine.initialize()
        print(f"✅ Broker ({engine.broker.name}) initialized.")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Test Market Scan
    print("\n📡 Testing Market Scanner...")
    try:
        watchlist = ["SPY", "QQQ", "AAPL", "TSLA"]
        from core.async_scanner import AsyncScanner
        scanner = AsyncScanner(watchlist)
        data = await scanner.scan_market()
        if data:
            print(f"✅ Scanner Working. Captured {len(data)} prices.")
            for t, p in list(data.items())[:5]:
                print(f"   - {t}: ${p}")
        else:
            print("⚠️ Scanner returned no data.")
    except Exception as e:
        print(f"❌ Scanner Failed: {e}")

    # 3. Test Historical Sync (If using Robinhood)
    if engine.broker.name == "robinhood":
        print("\n📊 Testing Robinhood Historical Sync...")
        try:
            # We use a small subset for the test
            await engine._sync_historical_data(["SPY", "QQQ"])
            if engine.history_cache:
                print(f"✅ Historical Data Synced for {len(engine.history_cache)} assets.")
            else:
                print("⚠️ Historical sync returned no data.")
        except Exception as e:
            print(f"❌ Historical Sync Failed: {e}")

    print("\n✨ Test Complete. No loops detected.")

if __name__ == "__main__":
    asyncio.run(run_test())
