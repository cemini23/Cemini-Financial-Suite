import asyncio
from typing import Dict, Any
from core.ems.base import BaseExecutionAdapter
from core.schemas.trading_signals import TradingSignal
from core.ems.adapters.kalshi_fix_client import KalshiFIXClient

class KalshiFIXAdapter(BaseExecutionAdapter):
    def __init__(self, host: str, port: int, sender_comp_id: str, target_comp_id: str):
        self.fix_client = KalshiFIXClient(host, port, sender_comp_id, target_comp_id)
        # We trigger the persistent connection
        asyncio.create_task(self.fix_client.connect_and_logon())

    async def get_buying_power(self) -> float:
        # In institutional setups, balance is often tracked locally via Execution Reports (35=8)
        # or queried via a separate REST management API.
        return 1000.00 

    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        if not self.fix_client.is_connected:
            return {"status": "error", "message": "FIX Session not connected"}
            
        # Standardizing quantities for prediction markets
        qty = 100 # Example fixed size
        price = 0.50 # Example limit price
        
        await self.fix_client.send_order(
            ticker=signal.ticker_or_event,
            action=signal.action,
            qty=qty,
            price=price
        )
        
        return {"status": "fix_order_dispatched", "ticker": signal.ticker_or_event}
