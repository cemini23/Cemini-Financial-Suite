"""Trade order and signal models.

Re-exports and extends the existing TradingSignal from
core/schemas/trading_signals.py. The envelope that flows through
the Redis trade_signals channel wraps TradingSignal in a dict.

Do NOT delete or modify core/schemas/trading_signals.py — it is used
directly by ems/main.py and core/ems/router.py.
"""

import logging
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Re-export existing TradingSignal so consumers can import from one place
try:
    from core.schemas.trading_signals import TradingSignal  # noqa: F401
    _TRADING_SIGNAL_AVAILABLE = True
except ImportError:
    _TRADING_SIGNAL_AVAILABLE = False
    logger.debug("core.schemas.trading_signals not importable from this path — OK in tests")


class TradeAction(str, Enum):
    """All valid trade action values used across signal payloads."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    SHORT = "short"
    COVER = "cover"
    CANCEL_ALL = "CANCEL_ALL"


class StrategyMode(str, Enum):
    """strategy_mode Redis key values (written by analyzer.py)."""

    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    SNIPER = "sniper"
    NEUTRAL = "neutral"
    STANDARD = "standard"


class TradeSignalEnvelope(BaseModel):
    """The dict published to the Redis trade_signals channel.

    Actual payload from signal_generator.py:
        {"pydantic_signal": {TradingSignal fields}, "timestamp": str,
         "strategy": "Intelligence_v1", "price": float, "rsi": float}
    """

    model_config = ConfigDict(extra="allow")

    pydantic_signal: Optional[dict[str, Any]] = None
    timestamp: Optional[Any] = None        # str or float from different producers
    strategy: Optional[str] = None
    price: Optional[float] = None
    rsi: Optional[float] = None
    reason: Optional[str] = None
    source: str = "unknown"


class TradeResult(BaseModel):
    """Execution result returned by EMS adapters."""

    model_config = ConfigDict(extra="allow")

    status: str = "unknown"             # "success" | "error" | "paper"
    order_id: Optional[str] = None
    ticker: Optional[str] = None
    action: Optional[str] = None
    price: Optional[float] = None
    message: Optional[str] = None
    source: str = "ems"
    timestamp: float = Field(default_factory=time.time)


class KillSwitchEvent(BaseModel):
    """Payload published to playbook:kill_switch channel by KillSwitch.

    Also used to structure the emergency_stop broadcast.
    Note: emergency_stop channel sends the raw string "CANCEL_ALL", not JSON.
    """

    model_config = ConfigDict(extra="allow")

    event: str = "kill_switch_triggered"
    reason: str = ""
    timestamp: Optional[float] = None
    source: str = "kill_switch"
