"""Regime classification models.

Matches the RegimeState dataclass in trading_playbook/macro_regime.py
and the payloads flowing through intel:playbook_snapshot.
"""

import logging
import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class RegimeClassification(str, Enum):
    """Macro regime labels used throughout the platform."""

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


class RegimeSnapshot(BaseModel):
    """Mirrors RegimeState.to_dict() from trading_playbook/macro_regime.py.

    Actual Redis payload under intel:playbook_snapshot.value.detail:
        {"regime": "RED", "spy_price": 673.575, "ema21": 685.1241,
         "sma50": 688.0739, "jnk_tlt_flag": false, "confidence": 0.8,
         "timestamp": 1772810466.63, "reason": "SPY 673.58 < SMA50 688.07"}
    """

    model_config = ConfigDict(extra="allow")

    regime: str = "UNKNOWN"
    spy_price: float = 0.0
    ema21: float = 0.0
    sma50: float = 0.0
    jnk_tlt_flag: bool = False
    confidence: float = 0.0
    timestamp: float = Field(default_factory=time.time)
    reason: str = ""


class PlaybookRegimePayload(BaseModel):
    """Shape published to intel:playbook_snapshot by playbook_logger.log_regime().

    Intel bus value field is:  {"regime": str, "detail": RegimeSnapshot-dict}
    """

    model_config = ConfigDict(extra="allow")

    regime: str = "UNKNOWN"
    detail: dict = Field(default_factory=dict)


class RegimeGateDecision(BaseModel):
    """Output from regime_gate.py — describes the gate verdict."""

    model_config = ConfigDict(extra="allow")

    allowed: bool = False
    regime: str = "UNKNOWN"
    confidence: float = 0.0
    reason: str = ""
    strategy_mode: Optional[str] = None
    source: str = "unknown"
    timestamp: float = Field(default_factory=time.time)
