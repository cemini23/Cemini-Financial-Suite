"""
Cemini Financial Suite — Trading Playbook Layer

Sits between the raw harvested data and the future RL model.
Provides regime classification, signal detection, risk controls, and
structured logging so the RL agent has labeled context to train against.

Components
----------
macro_regime    Traffic-light market regime classifier (GREEN/YELLOW/RED)
signal_catalog  Registry of discrete tactical setups with detect() methods
risk_engine     FractionalKelly sizing, CVaR, drawdown monitoring
kill_switch     Circuit breaker and master kill system
playbook_logger Structured JSON/Postgres logger bridging data to RL training
"""

from trading_playbook.macro_regime import RegimeState, classify_regime
from trading_playbook.signal_catalog import (
    EpisodicPivot,
    MomentumBurst,
    ElephantBar,
    VCP,
    HighTightFlag,
    InsideBar212,
    SIGNAL_REGISTRY,
)
from trading_playbook.risk_engine import FractionalKelly, CVaRCalculator, DrawdownMonitor
from trading_playbook.kill_switch import KillSwitch
from trading_playbook.playbook_logger import PlaybookLogger

__all__ = [
    "RegimeState",
    "classify_regime",
    "EpisodicPivot",
    "MomentumBurst",
    "ElephantBar",
    "VCP",
    "HighTightFlag",
    "InsideBar212",
    "SIGNAL_REGISTRY",
    "FractionalKelly",
    "CVaRCalculator",
    "DrawdownMonitor",
    "KillSwitch",
    "PlaybookLogger",
]
