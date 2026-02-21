import asyncio
import math
from typing import Dict, Any
from coinbase.rest import RESTClient
from core.ems.base import BaseExecutionAdapter
from core.schemas.trading_signals import TradingSignal

class CoinbaseAdapter(BaseExecutionAdapter):
    def __init__(self, api_key: str, api_secret: str):
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)

    async def get_buying_power(self) -> float:
        # Runs synchronously in the background via asyncio.to_thread
        accounts = await asyncio.to_thread(self.client.get_accounts)
        usd_account = next((acc for acc in accounts['accounts'] if acc['currency'] == 'USD'), None)
        return float(usd_account['available_balance']['value']) if usd_account else 0.0

    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        ticker = signal.ticker_or_event  # e.g., "BTC-USD"
        action = signal.action
        allocation = signal.proposed_allocation_pct
        
        buying_power = await self.get_buying_power()
        order_size = math.floor(buying_power * allocation)
        
        if action == "buy":
            response = await asyncio.to_thread(
                self.client.market_order_buy,
                client_order_id=f"quantos_{ticker}_{asyncio.get_event_loop().time()}",
                product_id=ticker,
                quote_size=str(order_size)
            )
            return response
        return {"status": "unsupported_action"}
