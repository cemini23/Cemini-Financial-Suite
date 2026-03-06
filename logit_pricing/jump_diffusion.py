"""logit_pricing.jump_diffusion — Regime classification and jump detection.

Shaw & Dalen (2025): binary contracts exhibit sudden probability jumps
(news events, resolution announcements) in addition to smooth diffusion.

In logit space, jumps are additive: a +2 logit jump roughly doubles the
odds ratio.

This module:
1. Detects individual jump events (|Δlogit| > threshold * σ_b)
2. Classifies regime: diffusion vs jump (elevated jump frequency)
3. Computes time-to-resolution decay factor
4. Does NOT try to predict jump direction — only recognizes jump regime
   and adjusts risk accordingly
"""
import math
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JUMP_SIGMA_THRESHOLD = 2.5   # |Δlogit| > 2.5σ → jump event
JUMP_REGIME_WINDOW = 20      # look-back count to assess jump frequency
JUMP_REGIME_MIN_RATE = 0.15  # ≥15% of observations are jumps → jump regime
JUMP_MIN_ABS_LOGIT = 0.20    # absolute minimum |Δlogit| for a jump (filters constant-delta noise)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class JumpEvent:
    """One detected jump in logit space."""
    index: int
    timestamp: float
    logit_before: float
    logit_after: float
    delta_logit: float
    sigma_multiple: float   # |delta_logit| / rolling_sigma


@dataclass
class RegimeState:
    """Regime classification result."""
    regime: str                       # "diffusion" | "jump"
    jump_count_window: int
    jump_rate: float
    rolling_sigma: float
    n_obs: int


# ---------------------------------------------------------------------------
# Jump detection
# ---------------------------------------------------------------------------

def detect_jumps(
    logits: np.ndarray,
    timestamps: Optional[np.ndarray] = None,
    sigma_threshold: float = JUMP_SIGMA_THRESHOLD,
    min_obs_for_sigma: int = 5,
) -> list[JumpEvent]:
    """Detect jump events in a logit time series.

    A jump is any |Δlogit| that exceeds sigma_threshold × rolling σ.
    Rolling σ is computed over the preceding min_obs_for_sigma changes.

    Args:
        logits:     1-D array of logit values (chronological)
        timestamps: optional unix timestamps matching logits
        sigma_threshold: multiplier for jump classification
        min_obs_for_sigma: min observations before sigma is reliable

    Returns:
        List of JumpEvent (may be empty if series is smooth)
    """
    logits = np.asarray(logits, dtype=np.float64)
    n = len(logits)
    if n < 2:
        return []

    deltas = np.diff(logits)
    events: list[JumpEvent] = []

    for idx in range(len(deltas)):
        # Rolling σ from preceding changes
        start = max(0, idx - min_obs_for_sigma)
        window = deltas[start:idx]
        if len(window) < 2:
            continue  # not enough history to compute σ
        rolling_sigma = float(np.std(window, ddof=1))
        d = float(deltas[idx])

        # Absolute minimum: very small moves are never jumps regardless of σ
        if abs(d) < JUMP_MIN_ABS_LOGIT:
            continue

        # Relative threshold: need both large σ-multiple AND non-trivial σ
        if rolling_sigma < 1e-9:
            # Near-zero local sigma with large absolute move → likely a jump
            # Use global series std as fallback
            global_sigma = float(np.std(deltas, ddof=1)) if len(deltas) >= 2 else 1e-9
            if global_sigma < 1e-9:
                continue
            sigma_mult = abs(d) / global_sigma
        else:
            sigma_mult = abs(d) / rolling_sigma

        if sigma_mult >= sigma_threshold:
            ts = float(timestamps[idx + 1]) if timestamps is not None else float(idx + 1)
            events.append(JumpEvent(
                index=idx + 1,
                timestamp=ts,
                logit_before=float(logits[idx]),
                logit_after=float(logits[idx + 1]),
                delta_logit=d,
                sigma_multiple=sigma_mult,
            ))

    return events


# ---------------------------------------------------------------------------
# Regime classification
# ---------------------------------------------------------------------------

def classify_regime(
    logits: np.ndarray,
    jumps: list[JumpEvent],
    window: int = JUMP_REGIME_WINDOW,
) -> RegimeState:
    """Classify the contract as diffusion or jump regime.

    Jump regime: ≥JUMP_REGIME_MIN_RATE of recent observations are jumps.
    Diffusion regime: infrequent or no jumps.

    In jump regime: widen confidence intervals, reduce position sizing.
    """
    n = len(logits)
    if n < 2:
        return RegimeState("diffusion", 0, 0.0, 0.0, n)

    deltas = np.diff(logits)
    recent_deltas = deltas[-window:]
    rolling_sigma = float(np.std(recent_deltas, ddof=1)) if len(recent_deltas) >= 2 else 0.0

    # Count jumps in the trailing window
    cutoff_idx = max(0, n - window)
    recent_jumps = [j for j in jumps if j.index >= cutoff_idx]
    jump_count = len(recent_jumps)
    jump_rate = jump_count / max(1, min(window, n - 1))

    regime = "jump" if jump_rate >= JUMP_REGIME_MIN_RATE else "diffusion"

    return RegimeState(
        regime=regime,
        jump_count_window=jump_count,
        jump_rate=jump_rate,
        rolling_sigma=rolling_sigma,
        n_obs=n,
    )


# ---------------------------------------------------------------------------
# Time-to-resolution decay
# ---------------------------------------------------------------------------

def time_decay_factor(
    resolution_timestamp: Optional[float],
    now: Optional[float] = None,
    max_horizon_days: float = 30.0,
) -> float:
    """Compute a time-decay factor for mean-reversion signal strength.

    As a binary contract approaches resolution, it converges to 0 or 1
    (pins to its outcome). The mean-reversion signal becomes less reliable
    near resolution — this factor discounts it.

    Returns:
        1.0 = far from resolution (full signal strength)
        0.0 = at or past resolution (signal completely off)

    Follows Shaw & Dalen τ = T-t convention.
    """
    if resolution_timestamp is None:
        return 1.0  # unknown expiry → full signal

    now = now or time.time()
    tau_seconds = resolution_timestamp - now
    if tau_seconds <= 0:
        return 0.0

    tau_days = tau_seconds / 86400.0
    # Linear decay, capped at max_horizon_days for normalization
    factor = min(1.0, tau_days / max_horizon_days)
    return float(factor)


# ---------------------------------------------------------------------------
# Fair value estimation
# ---------------------------------------------------------------------------

def fair_value_logit(
    logits: np.ndarray,
    regime: RegimeState,
    ema_span: int = 10,
) -> tuple[float, float]:
    """Estimate fair value logit and confidence.

    In diffusion regime: logit EMA is fair value.
    In jump regime: widen the confidence interval (return reduced confidence).

    Returns:
        (fair_value_logit, confidence)  confidence ∈ [0, 1]
    """
    from logit_pricing.indicators import logit_ema
    if len(logits) < 2:
        return float(logits[-1]) if len(logits) else 0.0, 0.0

    ema_vals = logit_ema(logits, span=ema_span)
    fair = float(ema_vals[-1])

    # Base confidence from data sufficiency
    data_conf = min(1.0, len(logits) / 30.0)

    # Jump regime penalty
    if regime.regime == "jump":
        jump_penalty = min(0.5, regime.jump_rate * 2.0)
        confidence = max(0.0, data_conf - jump_penalty)
    else:
        confidence = data_conf

    return fair, confidence
