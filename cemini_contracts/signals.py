"""Signal detection models.

Matches the dict shapes returned by BaseSetup.detect() in
trading_playbook/signal_catalog.py and consumed by playbook_runner.py.
"""

import logging
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """All signal patterns registered in the signal catalog."""

    EPISODIC_PIVOT = "EpisodicPivot"
    MOMENTUM_BURST = "MomentumBurst"
    ELEPHANT_BAR = "ElephantBar"
    VCP = "VCP"
    HIGH_TIGHT_FLAG = "HighTightFlag"
    INSIDE_BAR_212 = "InsideBar212"


class SignalDetection(BaseModel):
    """Represents one detected signal from the playbook signal catalog.

    Extra fields are allowed because each pattern adds its own keys
    (e.g. EpisodicPivot adds gap_pct; VCP adds num_contractions).
    """

    model_config = ConfigDict(extra="allow")

    symbol: str
    pattern_name: str
    detected: bool = True
    timestamp: float = Field(default_factory=time.time)
    regime_at_detection: Optional[str] = None
    source: str = "signal_catalog"

    # Common optional fields across patterns
    rsi: Optional[float] = None
    volume_ratio: Optional[float] = None
    close: Optional[float] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None


class SignalCatalogScan(BaseModel):
    """Result of scan_symbol() for one ticker across all detectors."""

    model_config = ConfigDict(extra="allow")

    symbol: str
    signals: list[SignalDetection] = Field(default_factory=list)
    regime: str = "UNKNOWN"
    timestamp: float = Field(default_factory=time.time)
    source: str = "playbook_runner"
