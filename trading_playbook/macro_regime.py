"""
Cemini Financial Suite — Macro Regime Classifier

Traffic-light market regime detector using SPY vs EMAs and JNK/TLT
cross-validation.

Regimes
-------
GREEN  → SPY above a rising 21-day EMA → full strategy activation
YELLOW → SPY below 21 EMA but above 50 SMA → defensive, no new longs
RED    → SPY below 50 SMA → survival mode, cash or short only

JNK/TLT cross-validation: if JNK underperforms TLT during an equity
breakout, flag it as a likely failed move (credit markets not confirming).

The regime state is published to the Intel Bus (intel:macro_regime) so all
other modules can consume it, and persisted via PlaybookLogger for the RL
training loop.
"""

import logging
import time
from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger("playbook.macro_regime")

# ----- constants ----------------------------------------------------------- #
EMA_FAST = 21        # SPY 21-day EMA (trend filter)
SMA_SLOW = 50        # SPY 50-day SMA (support/survival line)
EMA_RISING_BARS = 3  # look back N bars to confirm EMA slope
LOOKBACK_PERIOD = "3mo"   # yfinance period string — gives ~63 trading days
FETCH_TIMEOUT = 10   # seconds for yfinance network calls


# ----- data model ---------------------------------------------------------- #
@dataclass
class RegimeState:
    """Snapshot of the current macro market regime."""

    regime: str          # "GREEN", "YELLOW", or "RED"
    spy_price: float     # latest SPY closing price
    ema21: float         # current 21-day EMA value
    sma50: float         # current 50-day SMA value
    jnk_tlt_flag: bool   # True → credit NOT confirming equity breakout
    confidence: float    # 0.0 – 1.0 classifier confidence
    timestamp: float     # Unix epoch of classification
    reason: str          # human-readable explanation

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON / Redis storage."""
        return asdict(self)


# ----- helpers ------------------------------------------------------------- #
def _fetch_close(ticker: str, period: str = LOOKBACK_PERIOD) -> Optional[pd.Series]:
    """Return the closing price Series for *ticker* or None on failure."""
    try:
        df = yf.Ticker(ticker).history(period=period, timeout=FETCH_TIMEOUT)
        if df.empty:
            logger.warning("[MacroRegime] Empty yfinance response for %s", ticker)
            return None
        return df["Close"].dropna()
    except Exception as exc:
        logger.warning("[MacroRegime] yfinance fetch failed for %s: %s", ticker, exc)
        return None


def _ema(series: pd.Series, span: int) -> float:
    """Most recent EMA value."""
    return float(series.ewm(span=span, adjust=False).mean().iloc[-1])


def _sma(series: pd.Series, window: int) -> float:
    """Most recent SMA value."""
    return float(series.rolling(window=window).mean().iloc[-1])


def _ema_rising(series: pd.Series, span: int, lookback: int = EMA_RISING_BARS) -> bool:
    """True if the EMA trended upward over the last *lookback* bars."""
    ema_vals = series.ewm(span=span, adjust=False).mean()
    return float(ema_vals.iloc[-1]) > float(ema_vals.iloc[-lookback])


def _jnk_tlt_divergence(jnk: pd.Series, tlt: pd.Series, lookback: int = 5) -> bool:
    """
    Return True when JNK 5-day return < TLT 5-day return.

    During an equity breakout this signals that credit markets are NOT
    confirming the move — historically a precursor to failed breakouts.
    """
    if len(jnk) < lookback + 1 or len(tlt) < lookback + 1:
        return False
    jnk_ret = (float(jnk.iloc[-1]) - float(jnk.iloc[-lookback])) / float(jnk.iloc[-lookback])
    tlt_ret = (float(tlt.iloc[-1]) - float(tlt.iloc[-lookback])) / float(tlt.iloc[-lookback])
    return jnk_ret < tlt_ret


# ----- public API ---------------------------------------------------------- #
def classify_regime() -> RegimeState:
    """
    Classify the current macro market regime.

    Fetches SPY, JNK, and TLT OHLCV via yfinance (the macro harvesters
    already log Fear & Greed and 10Y yield to Redis; OHLCV series are
    fetched independently here to avoid coupling to harvester internals).

    Returns
    -------
    RegimeState
        Fully populated regime snapshot.  On data failure, regime defaults
        to RED with confidence 0.1 so the system stays defensive.
    """
    spy = _fetch_close("SPY")
    jnk = _fetch_close("JNK")
    tlt = _fetch_close("TLT")

    if spy is None or len(spy) < SMA_SLOW:
        logger.warning("[MacroRegime] Insufficient SPY data — defaulting to RED")
        return RegimeState(
            regime="RED",
            spy_price=0.0,
            ema21=0.0,
            sma50=0.0,
            jnk_tlt_flag=False,
            confidence=0.1,
            timestamp=time.time(),
            reason="Insufficient SPY data — defensive default",
        )

    spy_price = float(spy.iloc[-1])
    ema21_val = _ema(spy, EMA_FAST)
    sma50_val = _sma(spy, SMA_SLOW)
    ema21_up = _ema_rising(spy, EMA_FAST)

    # JNK/TLT cross-validation — only meaningful during equity breakout territory
    jnk_tlt_flag = False
    if jnk is not None and tlt is not None:
        if spy_price > ema21_val:   # equity breakout territory
            jnk_tlt_flag = _jnk_tlt_divergence(jnk, tlt)

    # ----- classify -------------------------------------------------------- #
    if spy_price > ema21_val and ema21_up:
        regime = "GREEN"
        confidence = 0.85
        reason = (
            f"SPY {spy_price:.2f} > EMA21 {ema21_val:.2f} (rising)"
        )
    elif spy_price > sma50_val:
        regime = "YELLOW"
        confidence = 0.70
        reason = (
            f"SPY {spy_price:.2f} < EMA21 {ema21_val:.2f} but > SMA50 {sma50_val:.2f}"
        )
    else:
        regime = "RED"
        confidence = 0.80
        reason = f"SPY {spy_price:.2f} < SMA50 {sma50_val:.2f}"

    if jnk_tlt_flag:
        confidence = round(max(0.45, confidence - 0.15), 4)
        reason += " | WARN: JNK underperforming TLT — failed breakout risk"

    return RegimeState(
        regime=regime,
        spy_price=round(spy_price, 4),
        ema21=round(ema21_val, 4),
        sma50=round(sma50_val, 4),
        jnk_tlt_flag=jnk_tlt_flag,
        confidence=confidence,
        timestamp=time.time(),
        reason=reason,
    )


def regime_from_prices(
    spy_close: np.ndarray,
    jnk_close: Optional[np.ndarray] = None,
    tlt_close: Optional[np.ndarray] = None,
) -> RegimeState:
    """
    Classify regime from pre-loaded numpy arrays (used in backtests / tests).

    Parameters
    ----------
    spy_close : np.ndarray
        Array of SPY closing prices, oldest first.  Minimum 50 values.
    jnk_close, tlt_close : np.ndarray, optional
        JNK and TLT closing prices for credit cross-validation.
    """
    spy = pd.Series(spy_close, dtype=float)
    jnk = pd.Series(jnk_close, dtype=float) if jnk_close is not None else None
    tlt = pd.Series(tlt_close, dtype=float) if tlt_close is not None else None

    if len(spy) < SMA_SLOW:
        return RegimeState(
            regime="RED",
            spy_price=0.0,
            ema21=0.0,
            sma50=0.0,
            jnk_tlt_flag=False,
            confidence=0.1,
            timestamp=time.time(),
            reason="Insufficient data for regime_from_prices",
        )

    spy_price = float(spy.iloc[-1])
    ema21_val = _ema(spy, EMA_FAST)
    sma50_val = _sma(spy, SMA_SLOW)
    ema21_up = _ema_rising(spy, EMA_FAST)

    jnk_tlt_flag = False
    if jnk is not None and tlt is not None and spy_price > ema21_val:
        jnk_tlt_flag = _jnk_tlt_divergence(jnk, tlt)

    if spy_price > ema21_val and ema21_up:
        regime = "GREEN"
        confidence = 0.85
        reason = f"SPY {spy_price:.2f} > EMA21 {ema21_val:.2f} (rising)"
    elif spy_price > sma50_val:
        regime = "YELLOW"
        confidence = 0.70
        reason = f"SPY {spy_price:.2f} < EMA21 {ema21_val:.2f} but > SMA50 {sma50_val:.2f}"
    else:
        regime = "RED"
        confidence = 0.80
        reason = f"SPY {spy_price:.2f} < SMA50 {sma50_val:.2f}"

    if jnk_tlt_flag:
        confidence = round(max(0.45, confidence - 0.15), 4)
        reason += " | WARN: JNK underperforming TLT — failed breakout risk"

    return RegimeState(
        regime=regime,
        spy_price=round(spy_price, 4),
        ema21=round(ema21_val, 4),
        sma50=round(sma50_val, 4),
        jnk_tlt_flag=jnk_tlt_flag,
        confidence=confidence,
        timestamp=time.time(),
        reason=reason,
    )
