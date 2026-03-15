"""Cemini Financial Suite — Pre-Live Safety Hardening (Step 49).

Seven safety sub-systems that form a defense-in-depth layer around
every live order path:

  49a  IdempotencyGuard   — cryptographic UUID + Redis SET NX dedup
  49b  Redis persistence  — AOF + RDB preamble config (docker-compose)
  49c  StateHydrator      — hydrate executed_trades / positions on restart
  49d  ExposureGate       — hard-blocking per-ticker exposure ceiling
  49e  HITLGate           — human-in-the-loop approval queue (Redis + Discord)
  49f  MFAHandler         — Robinhood TOTP via pyotp
  49g  SelfMatchLock      — Kalshi self-match prevention (CFTC requirement)
"""
from __future__ import annotations

from shared.safety.idempotency import IdempotencyGuard
from shared.safety.state_hydrator import StateHydrator
from shared.safety.exposure_gate import ExposureGate
from shared.safety.hitl_gate import HITLGate, HITLDecision
from shared.safety.mfa_handler import MFAHandler
from shared.safety.self_match_lock import SelfMatchLock

__all__ = [
    "IdempotencyGuard",
    "StateHydrator",
    "ExposureGate",
    "HITLGate",
    "HITLDecision",
    "MFAHandler",
    "SelfMatchLock",
]
