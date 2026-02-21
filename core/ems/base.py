import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any
from core.schemas.trading_signals import TradingSignal

class BaseExecutionAdapter(ABC):
    """The blueprint for all execution routing."""
    
    @abstractmethod
    async def get_buying_power(self) -> float:
        """Returns the available cash/margin in USD."""
        pass

    @abstractmethod
    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """Translates the Pydantic signal into a live brokerage API call."""
        pass
