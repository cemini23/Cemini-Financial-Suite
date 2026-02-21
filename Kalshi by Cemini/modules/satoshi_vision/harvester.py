import asyncio
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.vault import BTCHarvest
from modules.satoshi_vision.analyzer import SatoshiAnalyzer

class Harvester:
    """
    The Data Vault Harvester Daemon.
    Scrapes BTC market intelligence and commits it to SQLite every 5 minutes.
    """
    def __init__(self):
        self.analyzer = SatoshiAnalyzer()
        self.interval = 300 # 5 Minutes

    async def run(self):
        print("[*] Data Vault Harvester: ONLINE")
        while True:
            try:
                # 1. Fetch Market Intel
                data = await self.analyzer.analyze_btc_market()
                
                if data.get("status") != "error":
                    # 2. Map to Model
                    async with AsyncSessionLocal() as session:
                        async with session.begin():
                            inds = data.get("indicators", {})
                            harvest = BTCHarvest(
                                price=data["price"]["current"],
                                volume=0.0, 
                                rsi=inds.get("RSI", 0.0),
                                vwap=inds.get("VWAP", 0.0),
                                adx=inds.get("ADX", 0.0)
                            )
                            session.add(harvest)
                    print(f"[*] Harvester: BTC ${data['price']['current']} committed to Vault.")
                
            except Exception as e:
                print(f"[!] Harvester Error: {e}")
            
            await asyncio.sleep(self.interval)
