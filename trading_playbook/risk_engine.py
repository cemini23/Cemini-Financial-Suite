"""
Cemini Financial Suite — Risk Engine

Position sizing and portfolio risk controls.

Components
----------
FractionalKelly
    Computes optimal position size using the Kelly Criterion capped at a
    configurable fraction (default 25 %) to reduce variance.

CVaRCalculator
    Computes 99 % Conditional Value-at-Risk (Expected Shortfall) — the mean
    of returns in the worst 1 % tail.  More conservative than plain VaR.

DrawdownMonitor
    Tracks per-strategy and portfolio-level equity peaks; triggers hard halts
    when drawdown exceeds configurable thresholds.

All calculations are pure functions / lightweight stateful objects with no
network I/O.  The runner injects live data and decides what to do with the
results.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger("playbook.risk_engine")


# ============================================================================
# Fractional Kelly Criterion
# ============================================================================
class FractionalKelly:
    """
    Optimal position sizer based on the Kelly Criterion.

    Full Kelly fraction = W - (1 - W) / R
    where W = win_rate, R = avg_win / avg_loss (reward-to-risk ratio).

    A fractional Kelly (e.g., 25 %) is applied to limit variance and model
    error.  The result is the recommended fraction of capital to risk on a
    single trade.

    Parameters
    ----------
    fraction : float
        Multiplier applied to full Kelly, in the range (0, 1].
        Default 0.25 (25 % of full Kelly).
    """

    def __init__(self, fraction: float = 0.25):
        if not 0 < fraction <= 1.0:
            raise ValueError(f"fraction must be in (0, 1], got {fraction}")
        self.fraction = fraction

    def calculate(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """
        Compute the fractional Kelly position size.

        Parameters
        ----------
        win_rate : float   Fraction of trades that are winners (0–1).
        avg_win  : float   Average dollar (or %) gain on a winning trade.
        avg_loss : float   Average dollar (or %) loss on a losing trade (positive).

        Returns
        -------
        float
            Fraction of capital to allocate (0 – fraction).  Returns 0.0
            when Kelly is negative (no edge) or inputs are invalid.
        """
        if avg_loss <= 0 or avg_win <= 0:
            logger.debug("[FractionalKelly] avg_win or avg_loss <= 0 — returning 0")
            return 0.0
        if not 0.0 <= win_rate <= 1.0:
            logger.debug("[FractionalKelly] win_rate out of range: %s — returning 0", win_rate)
            return 0.0

        reward_ratio = avg_win / avg_loss
        full_kelly = win_rate - (1.0 - win_rate) / reward_ratio
        full_kelly = max(0.0, min(1.0, full_kelly))

        result = round(full_kelly * self.fraction, 6)
        logger.debug(
            "[FractionalKelly] win=%.3f R=%.3f → full=%.4f → frac(%.2f)=%.4f",
            win_rate, reward_ratio, full_kelly, self.fraction, result,
        )
        return result

    def max_allocation(self) -> float:
        """Return the theoretical maximum allocation (fraction × 1.0)."""
        return self.fraction


# ============================================================================
# CVaR (Expected Shortfall)
# ============================================================================
class CVaRCalculator:
    """
    99 % Conditional Value-at-Risk (CVaR / Expected Shortfall).

    CVaR at confidence level α is the expected return *given* that the
    return falls in the worst (1 − α) tail.  At 99 % confidence this is the
    mean of the worst 1 % of observed returns.

    CVaR is strictly more conservative than VaR: it captures the *magnitude*
    of tail losses, not just the threshold.

    Parameters
    ----------
    confidence : float   Default 0.99 (99 %).
    """

    def __init__(self, confidence: float = 0.99):
        if not 0 < confidence < 1:
            raise ValueError(f"confidence must be in (0, 1), got {confidence}")
        self.confidence = confidence

    def calculate(self, returns: np.ndarray) -> float:
        """
        Compute CVaR from a 1-D array of P&L returns.

        Parameters
        ----------
        returns : np.ndarray
            Array of daily (or periodic) returns.  Losses are negative values.
            Minimum 20 observations recommended; returns 0.0 for < 10 obs.

        Returns
        -------
        float
            CVaR as a negative number (expected loss in the tail).
            Returns 0.0 when there is insufficient data.
        """
        arr = np.asarray(returns, dtype=float)
        arr = arr[np.isfinite(arr)]

        if len(arr) < 10:
            logger.debug("[CVaR] Fewer than 10 finite returns — returning 0.0")
            return 0.0

        cutoff_pct = (1.0 - self.confidence) * 100.0
        var_threshold = float(np.percentile(arr, cutoff_pct))
        tail = arr[arr <= var_threshold]

        if len(tail) == 0:
            return float(var_threshold)

        cvar = float(np.mean(tail))
        logger.debug("[CVaR] %.0f%% CVaR = %.6f  (VaR threshold = %.6f)", self.confidence * 100, cvar, var_threshold)
        return cvar

    def exceeds_limit(self, returns: np.ndarray, nav: float, limit_pct: float = 0.05) -> bool:
        """
        Return True if CVaR in dollar terms exceeds *limit_pct* of NAV.

        Parameters
        ----------
        returns     : np.ndarray   Daily return series (fractional, e.g. -0.02).
        nav         : float        Net Asset Value in dollars.
        limit_pct   : float        Hard limit as fraction of NAV.  Default 5 %.
        """
        cvar = self.calculate(returns)
        dollar_loss = abs(cvar) * nav
        limit_dollars = abs(limit_pct) * nav
        exceeded = dollar_loss > limit_dollars
        if exceeded:
            logger.warning(
                "[CVaR] Limit breached: |CVaR| $%.2f > limit $%.2f (%.1f%% NAV)",
                dollar_loss, limit_dollars, limit_pct * 100,
            )
        return exceeded


# ============================================================================
# Drawdown Monitor
# ============================================================================
@dataclass
class _StrategyState:
    peak_equity: float = 0.0
    halted: bool = False
    halt_reason: str = ""
    halt_time: float = 0.0


class DrawdownMonitor:
    """
    Tracks equity peaks per strategy and fires hard halts on breach.

    Each strategy is identified by a string name.  When the drawdown from
    peak exceeds *threshold*, the strategy is marked as halted and
    quarantined until manually reset.

    Parameters
    ----------
    threshold : float
        Maximum tolerated drawdown from equity peak as a fraction (0–1).
        Default 0.15 (15 %).
    """

    def __init__(self, threshold: float = 0.15):
        if not 0 < threshold <= 1.0:
            raise ValueError(f"threshold must be in (0, 1], got {threshold}")
        self.threshold = threshold
        self._strategies: Dict[str, _StrategyState] = {}

    def update(self, strategy: str, equity: float) -> Optional[str]:
        """
        Update equity for *strategy* and check for drawdown breach.

        Parameters
        ----------
        strategy : str    Strategy name / identifier.
        equity   : float  Current equity value.

        Returns
        -------
        str or None
            Halt reason string if drawdown breached (strategy is now halted),
            else None.
        """
        if strategy not in self._strategies:
            self._strategies[strategy] = _StrategyState(peak_equity=equity)

        state = self._strategies[strategy]

        if state.halted:
            return state.halt_reason   # already quarantined

        if equity > state.peak_equity:
            state.peak_equity = equity

        if state.peak_equity > 0:
            drawdown = (state.peak_equity - equity) / state.peak_equity
            if drawdown >= self.threshold:
                reason = (
                    f"[DrawdownMonitor] {strategy} halted: drawdown "
                    f"{drawdown:.2%} >= threshold {self.threshold:.2%} "
                    f"(peak={state.peak_equity:.2f}, current={equity:.2f})"
                )
                state.halted = True
                state.halt_reason = reason
                state.halt_time = time.time()
                logger.warning(reason)
                return reason

        return None

    def is_halted(self, strategy: str) -> bool:
        """Return True if *strategy* is currently quarantined."""
        return self._strategies.get(strategy, _StrategyState()).halted

    def reset(self, strategy: str) -> None:
        """
        Manually re-arm *strategy* after review.

        Should only be called after root-cause investigation.
        """
        if strategy in self._strategies:
            state = self._strategies[strategy]
            state.halted = False
            state.halt_reason = ""
            state.halt_time = 0.0
            logger.info("[DrawdownMonitor] %s manually reset and re-armed", strategy)

    def snapshot(self) -> dict:
        """Return a dict snapshot of all strategy states (for logging)."""
        return {
            name: {
                "peak_equity": s.peak_equity,
                "halted": s.halted,
                "halt_reason": s.halt_reason,
            }
            for name, s in self._strategies.items()
        }

    # ---------------------------------------------------------------------- #
    # Portfolio-level helpers
    # ---------------------------------------------------------------------- #
    @staticmethod
    def portfolio_drawdown(equity_curve: np.ndarray) -> float:
        """
        Compute the current drawdown of a portfolio equity curve.

        Parameters
        ----------
        equity_curve : np.ndarray
            Series of equity values, oldest first.

        Returns
        -------
        float
            Current drawdown as a positive fraction (0 = at peak, 1 = total loss).
        """
        arr = np.asarray(equity_curve, dtype=float)
        if len(arr) == 0:
            return 0.0
        peak = float(np.maximum.accumulate(arr)[-1])
        current = float(arr[-1])
        if peak <= 0:
            return 0.0
        return max(0.0, (peak - current) / peak)


# ============================================================================
# Convenience factory
# ============================================================================
def build_risk_engine(
    kelly_fraction: float = 0.25,
    cvar_confidence: float = 0.99,
    drawdown_threshold: float = 0.15,
) -> dict:
    """
    Instantiate all three risk components with consistent parameters.

    Returns
    -------
    dict with keys: "kelly", "cvar", "drawdown"
    """
    return {
        "kelly": FractionalKelly(fraction=kelly_fraction),
        "cvar": CVaRCalculator(confidence=cvar_confidence),
        "drawdown": DrawdownMonitor(threshold=drawdown_threshold),
    }


# Module-level defaults used by runner.py
_default_engine: dict = field(default_factory=dict) if False else {}  # placeholder
