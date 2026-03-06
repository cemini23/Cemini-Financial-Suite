"""logit_pricing.pricing_engine — Main LogitPricingEngine.

Orchestrates transforms → indicators → jump_diffusion → ContractAssessment.

Usage:
    engine = LogitPricingEngine()
    assessment = engine.assess_contract(prices, timestamps, resolution_ts, current_price)

Thread-safe: all state is passed in; engine holds no per-contract mutable state.
"""
import logging
import math
import time
from typing import Optional

import numpy as np

from logit_pricing.transforms import (
    logit, inv_logit, logit_array, logit_mid, logit_spread, P_MIN, P_MAX,
)
from logit_pricing.indicators import (
    logit_ema, logit_sma, logit_bollinger, logit_rsi,
    logit_mean_reversion_score, implied_belief_vol,
)
from logit_pricing.jump_diffusion import (
    detect_jumps, classify_regime, time_decay_factor, fair_value_logit,
)
from logit_pricing.precision import assert_finite, sanitize_array
from logit_pricing.models import ContractAssessment

logger = logging.getLogger("logit_pricing.engine")

MIN_OBSERVATIONS = 10    # minimum price history for a reliable assessment
EMA_SPAN = 10            # logit EMA span for fair value
SMA_WINDOW = 10          # logit SMA window
BB_WINDOW = 20           # Bollinger band window
RSI_PERIOD = 14          # Wilder RSI period

# Environment variable for exit sensitivity (σ multiplier)
import os
LOGIT_EXIT_SENSITIVITY = float(os.getenv("LOGIT_EXIT_SENSITIVITY", "1.0"))

# Default Avellaneda-Stoikov params (calibratable)
GAMMA_DEFAULT = 0.08
K_DEFAULT = 1.4


class LogitPricingEngine:
    """Evaluates Kalshi contract mispricing using logit-space analysis.

    Shaw & Dalen (2025) framework:
    1. Transform price history to logit space
    2. Compute logit-space TA (EMA, Bollinger, Wilder RSI)
    3. Detect jumps via rolling σ threshold
    4. Classify regime (diffusion vs jump)
    5. Compute mean-reversion score normalized by logit volatility
    6. Apply time-to-resolution decay
    7. Return ContractAssessment with all fields validated
    """

    def assess_contract(
        self,
        prices: list[float],
        timestamps: Optional[list[float]] = None,
        resolution_timestamp: Optional[float] = None,
        current_price: Optional[float] = None,
        ticker: str = "",
        yes_bid: Optional[float] = None,
        yes_ask: Optional[float] = None,
    ) -> ContractAssessment:
        """Assess a binary contract for mispricing.

        Args:
            prices:               Historical yes_bid prices on 0-1 scale
            timestamps:           Unix timestamps matching prices (optional)
            resolution_timestamp: Unix timestamp of contract resolution (optional)
            current_price:        Latest price to assess (defaults to last in prices)
            ticker:               Market ticker string for logging/display
            yes_bid, yes_ask:     Current bid/ask for spread calibration (optional)

        Returns:
            ContractAssessment with mispricing_score and all indicators
        """
        n = len(prices)

        # Insufficient data — return low-confidence default
        if n < 2:
            return ContractAssessment(
                ticker=ticker,
                current_price=float(current_price or 0.5),
                logit_current=logit(float(current_price or 0.5)),
                n_observations=n,
                is_sufficient=False,
                confidence=0.0,
                yes_bid=yes_bid,
                yes_ask=yes_ask,
            )

        prices_arr = np.array([float(p) for p in prices], dtype=np.float64)
        ts_arr = np.array(timestamps, dtype=np.float64) if timestamps else None

        # ── 1. Logit transform ────────────────────────────────────────────────
        logits, invalid_mask = logit_array(prices_arr)
        if invalid_mask.sum() > n * 0.3:
            logger.warning("%s: >30%% invalid prices, skipping", ticker)
            return ContractAssessment(ticker=ticker, n_observations=n)

        # ── 2. Current logit ──────────────────────────────────────────────────
        cur_p = float(current_price) if current_price is not None else float(prices_arr[-1])
        cur_p = max(P_MIN, min(P_MAX, cur_p))
        cur_logit = logit(cur_p)

        # ── 3. Logit-space TA indicators ──────────────────────────────────────
        ema_vals = logit_ema(logits, span=EMA_SPAN)
        sma_vals = logit_sma(logits, window=min(SMA_WINDOW, n))
        rsi_vals = logit_rsi(logits, period=min(RSI_PERIOD, max(2, n // 2)))

        bb_upper, bb_mid, bb_lower = logit_bollinger(
            logits, window=min(BB_WINDOW, n), num_std=2.0
        )

        ema_now = float(ema_vals[-1]) if np.isfinite(ema_vals[-1]) else cur_logit
        sma_now = float(sma_vals[-1]) if np.isfinite(sma_vals[-1]) else cur_logit
        rsi_now = float(rsi_vals[-1]) if np.isfinite(rsi_vals[-1]) else 50.0
        bb_u = float(bb_upper[-1]) if np.isfinite(bb_upper[-1]) else cur_logit + 1.0
        bb_l = float(bb_lower[-1]) if np.isfinite(bb_lower[-1]) else cur_logit - 1.0
        bb_m = float(bb_mid[-1]) if np.isfinite(bb_mid[-1]) else ema_now

        # ── 4. Rolling logit volatility ───────────────────────────────────────
        deltas = np.diff(logits)
        recent_window = deltas[-min(20, len(deltas)):]
        logit_vol = float(np.std(recent_window, ddof=1)) if len(recent_window) >= 2 else 0.0

        # ── 5. Jump detection and regime classification ───────────────────────
        jumps = detect_jumps(logits, ts_arr)
        regime_state = classify_regime(logits, jumps)

        # ── 6. Fair value and confidence ──────────────────────────────────────
        fv_logit, base_conf = fair_value_logit(logits, regime_state, ema_span=EMA_SPAN)
        fv_prob = inv_logit(fv_logit)

        # ── 7. Mispricing score ───────────────────────────────────────────────
        # Score > 0 = overpriced (logit above EMA), < 0 = underpriced
        misprice = logit_mean_reversion_score(cur_logit, fv_logit, logit_vol)

        # ── 8. Time-to-resolution decay ───────────────────────────────────────
        td = time_decay_factor(resolution_timestamp)
        # Decay discounts the mispricing signal near resolution
        effective_conf = base_conf * td

        # ── 9. Implied belief volatility (Shaw & Dalen §4) ───────────────────
        sigma_b = 0.0
        if yes_bid is not None and yes_ask is not None and td > 0:
            tau_years = td * 30.0 / 365.0  # rough: td=1 → ~30 days out
            sigma_b = implied_belief_vol(yes_bid, yes_ask, tau=max(1e-6, tau_years))

        # ── 10. Validate all outputs ──────────────────────────────────────────
        for val, ctx in [
            (cur_logit, "cur_logit"), (fv_logit, "fv_logit"),
            (misprice, "misprice"), (logit_vol, "logit_vol"),
        ]:
            if not math.isfinite(val):
                logger.warning("%s: non-finite %s=%s — zeroing", ticker, ctx, val)
                if ctx == "misprice":
                    misprice = 0.0
                elif ctx == "logit_vol":
                    logit_vol = 0.0

        is_sufficient = n >= MIN_OBSERVATIONS

        return ContractAssessment(
            ticker=ticker,
            current_price=cur_p,
            logit_current=cur_logit,
            logit_fair_value=fv_logit,
            fair_value_probability=fv_prob,
            mispricing_score=float(np.clip(misprice, -3.0, 3.0)),
            regime=regime_state.regime,
            confidence=round(float(np.clip(effective_conf, 0.0, 1.0)), 4),
            time_decay_factor=round(td, 4),
            jump_count_window=regime_state.jump_count_window,
            logit_volatility=round(logit_vol, 6),
            implied_sigma_b=round(sigma_b, 6),
            indicators={
                "logit_ema": round(ema_now, 6),
                "logit_sma": round(sma_now, 6),
                "logit_rsi": round(rsi_now, 2),
                "logit_bb_upper": round(bb_u, 6),
                "logit_bb_lower": round(bb_l, 6),
                "logit_bb_mid": round(bb_m, 6),
            },
            n_observations=n,
            is_sufficient=is_sufficient,
            yes_bid=yes_bid,
            yes_ask=yes_ask,
        )

    def logit_exit_signal(
        self,
        assessment: ContractAssessment,
        position_side: str = "yes",
    ) -> dict:
        """Determine if a logit-space signal warrants early exit.

        Supplements the hardcoded 90c TP / 10c SL backstops in autopilot.
        Fires BEFORE the backstops when mean-reversion has completed.

        Args:
            assessment:     ContractAssessment for the held contract
            position_side:  "yes" or "no" (direction of held position)

        Returns:
            {"exit": bool, "reason": str, "confidence": float}
        """
        if not assessment.is_sufficient:
            return {"exit": False, "reason": "insufficient_data", "confidence": 0.0}

        if assessment.regime == "jump":
            # Jump regime: tighter stops — any move against position is more
            # likely to continue than mean-revert
            threshold = LOGIT_EXIT_SENSITIVITY * 0.5   # tighter in jump regime
        else:
            threshold = LOGIT_EXIT_SENSITIVITY

        score = assessment.mispricing_score
        conf = assessment.confidence

        if position_side == "yes":
            # Holding YES: exit when price has mean-reverted ABOVE fair value
            # (score > threshold means overpriced now → take profit on YES)
            if score > threshold and conf > 0.3:
                return {
                    "exit": True,
                    "reason": f"logit_mean_reversion_tp (score={score:.2f}, threshold={threshold:.2f})",
                    "confidence": conf,
                }
        else:  # "no"
            # Holding NO: exit when price has mean-reverted BELOW fair value
            if score < -threshold and conf > 0.3:
                return {
                    "exit": True,
                    "reason": f"logit_mean_reversion_tp (score={score:.2f}, threshold={threshold:.2f})",
                    "confidence": conf,
                }

        return {"exit": False, "reason": "no_signal", "confidence": conf}
