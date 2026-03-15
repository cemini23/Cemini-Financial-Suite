"""Cemini Financial Suite — Pydantic Data Contracts v1.0

Shared typed models for all cross-service boundaries.

Usage:
    from cemini_contracts import RegimeSnapshot, TradeOrder, PlaybookLog
    from cemini_contracts._compat import safe_validate, safe_dump
"""

from cemini_contracts.market import *       # noqa: F401,F403
from cemini_contracts.intel import *        # noqa: F401,F403
from cemini_contracts.regime import *       # noqa: F401,F403
from cemini_contracts.signals import *      # noqa: F401,F403
from cemini_contracts.risk import *         # noqa: F401,F403
from cemini_contracts.trade import *        # noqa: F401,F403
from cemini_contracts.discovery import *    # noqa: F401,F403
from cemini_contracts.playbook import *     # noqa: F401,F403
from cemini_contracts.kalshi import *       # noqa: F401,F403
from cemini_contracts._compat import safe_validate, safe_dump  # noqa: F401
from cemini_contracts.vector import *        # noqa: F401,F403

__version__ = "1.0.0"
from cemini_contracts.pricing import *       # noqa: F401,F403
from cemini_contracts.fred import *          # noqa: F401,F403
from cemini_contracts.sector import *        # noqa: F401,F403
