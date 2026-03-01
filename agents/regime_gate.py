# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
"""
Dynamic regime confidence threshold gate.

Pure module — no I/O, no Redis, no Postgres.  Importable in tests without
any infrastructure dependencies.

The gate replaces the old binary BUY blocker: instead of going blind in
YELLOW/RED, the system gets PICKIER.  BUY confidence requirements rise with
regime severity; SELL/SHORT requirements fall (easier to reduce exposure).

EpisodicPivot and InsideBar212 receive a +0.10 catalyst bonus in YELLOW/RED
because they represent new information events (earnings gaps, compression
breakouts) that can override the macro environment.  Trend-continuation
patterns (MomentumBurst, ElephantBar, VCP, HighTightFlag) genuinely
underperform in bad regimes and receive no bonus.

The kill switch (emergency_stop Redis channel) still overrides everything —
this module has no knowledge of it.
"""

# ── Threshold table ──────────────────────────────────────────────────────────
# BUY:        threshold rises in worse regimes (pickier entries).
# SELL/SHORT: threshold falls in worse regimes (easier exits).
REGIME_THRESHOLDS: dict[str, dict[str, float]] = {
    "GREEN":  {"BUY": 0.55, "SELL": 0.55, "SHORT": 0.55},
    "YELLOW": {"BUY": 0.75, "SELL": 0.50, "SHORT": 0.50},
    "RED":    {"BUY": 0.85, "SELL": 0.45, "SHORT": 0.45},
}

# Catalyst-driven patterns that earn a confidence bonus in YELLOW/RED.
CATALYST_PATTERNS: frozenset = frozenset({"EpisodicPivot", "InsideBar212"})
CATALYST_BONUS: float = 0.10

# Permissive fallback when no regime data is available on the Intel Bus.
_REGIME_FALLBACK = "GREEN"


def _regime_gate(
    action: str,
    confidence: float,
    regime,
    signal_type: str = "",
) -> tuple:
    """
    Dynamic confidence threshold gate.

    Parameters
    ----------
    action      : "BUY", "SELL", "SHORT" (case-insensitive)
    confidence  : raw signal confidence from CIO debate (0.0–1.0)
    regime      : "GREEN", "YELLOW", "RED", or None
    signal_type : optional playbook pattern name for catalyst bonus

    Returns
    -------
    (blocked: bool, effective_confidence: float, reason: str)
    ``reason`` is "" when the signal passes the gate.
    """
    action_upper = action.upper()
    resolved_regime = regime if regime in REGIME_THRESHOLDS else _REGIME_FALLBACK
    thresholds = REGIME_THRESHOLDS[resolved_regime]
    threshold = thresholds.get(action_upper, thresholds["BUY"])

    # Catalyst bonus: EpisodicPivot / InsideBar212 only in YELLOW/RED
    effective_confidence = confidence
    bonus_note = ""
    if resolved_regime in ("YELLOW", "RED") and signal_type in CATALYST_PATTERNS:
        effective_confidence = min(1.0, confidence + CATALYST_BONUS)
        bonus_note = (
            f" +{CATALYST_BONUS:.2f} {signal_type} catalyst"
            f" \u2192 {effective_confidence:.2f}"
        )

    if effective_confidence < threshold:
        reason = (
            f"\u26a0\ufe0f Signal below regime threshold: "
            f"confidence={confidence:.2f}{bonus_note}, "
            f"required={threshold:.2f}, regime={resolved_regime}"
        )
        return True, effective_confidence, reason

    return False, effective_confidence, ""
