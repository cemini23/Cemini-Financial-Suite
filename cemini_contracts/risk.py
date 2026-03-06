"""Risk assessment models.

Matches the payload shapes in trading_playbook/risk_engine.py and
the log_risk_snapshot() call in playbook_logger.py.
"""

import logging
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class CVaRResult(BaseModel):
    """Output from CVaRCalculator."""

    model_config = ConfigDict(extra="allow")

    cvar_99: float = 0.0
    percentile: float = 99.0
    window_size: int = 0
    source: str = "CVaRCalculator"
    timestamp: float = Field(default_factory=time.time)


class KellyResult(BaseModel):
    """Output from FractionalKelly.size()."""

    model_config = ConfigDict(extra="allow")

    kelly_size: float = 0.0
    raw_kelly: float = 0.0
    fraction: float = 0.25
    cap: float = 0.25
    source: str = "FractionalKelly"
    timestamp: float = Field(default_factory=time.time)


class DrawdownSnapshot(BaseModel):
    """Output from DrawdownMonitor.snapshot()."""

    model_config = ConfigDict(extra="allow")

    peak: float = 0.0
    current: float = 0.0
    drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    in_drawdown: bool = False


class RiskAssessment(BaseModel):
    """Matches the payload written by playbook_logger.log_risk_snapshot().

    Actual dict keys: cvar_99, kelly_size, nav, drawdown_snapshot
    """

    model_config = ConfigDict(extra="allow")

    cvar_99: float = 0.0
    kelly_size: float = 0.0
    nav: float = 0.0
    drawdown_snapshot: dict[str, Any] = Field(default_factory=dict)
    source: str = "risk_engine"
    timestamp: float = Field(default_factory=time.time)
