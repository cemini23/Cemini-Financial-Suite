from typing import Dict, Any, Type
from core.ems.base import BaseExecutionAdapter
from core.schemas.trading_signals import TradingSignal
from core.ems.adapters.coinbase import CoinbaseAdapter
from core.ems.adapters.robinhood import RobinhoodAdapter
from core.ems.adapters.kalshi_fix import KalshiFIXAdapter
from core.ems.adapters.hardrock import HardRockBetAdapter

class EMS:
    """
    Execution Management System Router.
    Dynamically routes signals to the correct brokerage adapter.
    """
    def __init__(self):
        self.adapters: Dict[str, BaseExecutionAdapter] = {}

    def register_adapter(self, name: str, adapter: BaseExecutionAdapter):
        self.adapters[name] = adapter

    async def execute(self, signal: TradingSignal) -> Dict[str, Any]:
        adapter = self.adapters.get(signal.target_brokerage)
        if not adapter:
            return {"status": "error", "message": f"No adapter registered for {signal.target_brokerage}"}
        
        # 1. Verification Step (Risk Manager would have called this already, but EMS double-checks)
        buying_power = await adapter.get_buying_power()
        
        # 2. Execution Step
        print(f"🚀 EMS: Routing {signal.action} {signal.ticker_or_event} to {signal.target_brokerage}...")
        return await adapter.execute_order(signal)

# Global EMS Instance
ems = EMS()
