"""Cemini Financial Suite — Debate Tie-Breaker (Step 47).

Deterministic regime-weighted scoring. Pure Python — no LLM, fully auditable.

Regime multipliers:
  GREEN  → bull_score × 1.2  (rising market, favour bulls)
  RED    → bear_score × 1.2  (falling market, favour bears)
  YELLOW → no multiplier     (neutral — pure score comparison)
"""
from __future__ import annotations

from typing import Literal

from debate_protocol.config import (
    CLOSE_CALL_THRESHOLD,
    REGIME_BEAR_MULTIPLIER,
    REGIME_BULL_MULTIPLIER,
    TIE_THRESHOLD,
)

Action = Literal["BUY", "SELL", "HOLD", "NO_ACTION"]


def resolve(
    bull_score: float,
    bear_score: float,
    regime: str,
    threshold: float = TIE_THRESHOLD,
    close_call_threshold: float = CLOSE_CALL_THRESHOLD,
) -> tuple[Action, bool, bool]:
    """Apply regime-weighted tie-breaking and return a verdict.

    Args:
        bull_score:          Aggregated bull confidence score (≥ 0).
        bear_score:          Aggregated bear confidence score (≥ 0).
        regime:              Market regime: "GREEN" | "YELLOW" | "RED".
        threshold:           Minimum margin to avoid HOLD (default 0.10).
        close_call_threshold: Margin below which tie_break_used is flagged (default 0.20).

    Returns:
        Tuple of:
          action               — "BUY" | "SELL" | "HOLD"
          regime_multiplier_applied — whether a regime multiplier was used
          tie_break_used       — whether the result was close (margin < close_call_threshold)
    """
    regime_upper = regime.upper()
    multiplier_applied = False

    if regime_upper == "GREEN":
        bull_score = bull_score * REGIME_BULL_MULTIPLIER
        multiplier_applied = True
    elif regime_upper == "RED":
        bear_score = bear_score * REGIME_BEAR_MULTIPLIER
        multiplier_applied = True

    margin = bull_score - bear_score

    if abs(margin) < threshold:
        # True tie — conservative default
        return "HOLD", multiplier_applied, True

    action: Action = "BUY" if margin > 0 else "SELL"
    tie_break_used = abs(margin) < close_call_threshold

    return action, multiplier_applied, tie_break_used
