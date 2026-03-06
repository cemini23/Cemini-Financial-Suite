"""Playbook log models.

Matches the record schema written by PlaybookLogger to Postgres,
JSONL disk archives, and the intel:playbook_snapshot Redis key.

Log record schema (from playbook_logger.py docstring):
    {"timestamp": float, "log_type": str, "regime": str|null, "payload": dict}
"""

import logging
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class PlaybookLogType(str, Enum):
    """All log_type values used by PlaybookLogger."""

    REGIME = "regime"
    SIGNAL = "signal"
    RISK = "risk"
    KILL_SWITCH = "kill_switch"


class PlaybookLog(BaseModel):
    """One record written to playbook_logs and the JSONL archives.

    Actual schema confirmed from playbook_logger._write():
        {"timestamp": float, "log_type": str, "regime": str|null, "payload": dict}
    """

    model_config = ConfigDict(extra="allow")

    timestamp: float = Field(default_factory=time.time)
    log_type: str                          # PlaybookLogType value
    regime: Optional[str] = None           # GREEN | YELLOW | RED | null
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = "playbook_logger"


class PlaybookSnapshot(BaseModel):
    """Shape published to intel:playbook_snapshot by PlaybookLogger._redis_publish().

    This is the INNER value (stored in IntelPayload.value):
        {"regime": "RED", "detail": {RegimeSnapshot fields}}
    or
        {"latest_signal": {SignalDetection fields}}
    """

    model_config = ConfigDict(extra="allow")

    # regime snapshot variant
    regime: Optional[str] = None
    detail: Optional[dict[str, Any]] = None

    # signal variant
    latest_signal: Optional[dict[str, Any]] = None
