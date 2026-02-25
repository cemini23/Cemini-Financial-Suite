"""
Cemini Financial Suite — Signal Catalog

Registry of discrete tactical setups.  Each setup exposes a detect() method
that accepts a pandas OHLCV DataFrame and returns a signal dict or None.

Signal dict schema
------------------
{
    "pattern_name": str,       # e.g. "EpisodicPivot"
    "symbol":       str,       # ticker symbol
    "confidence":   float,     # 0.0 – 1.0
    "entry_price":  float,     # suggested entry (usually just-above a pivot)
    "stop_price":   float,     # hard stop loss price
    "detected_at":  str,       # ISO-8601 UTC timestamp
    "metadata":     dict,      # pattern-specific supporting data
}

OHLCV DataFrame contract
------------------------
Must contain columns: Open, High, Low, Close, Volume (case-sensitive).
Index does not matter.  Rows are chronological (oldest first).
Minimum row count varies per detector (see each class docstring).

No live orders are placed here — detectors are read-only.  Execution comes
later with the RL agent.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("playbook.signal_catalog")

# ----- required columns ----------------------------------------------------- #
_REQUIRED_COLS = {"Open", "High", "Low", "Close", "Volume"}


def _validate(df: pd.DataFrame, min_rows: int, caller: str) -> bool:
    """Return True if *df* is valid; log and return False otherwise."""
    if not _REQUIRED_COLS.issubset(df.columns):
        missing = _REQUIRED_COLS - set(df.columns)
        logger.debug("[%s] Missing columns: %s", caller, missing)
        return False
    if len(df) < min_rows:
        logger.debug("[%s] Need >= %d rows, got %d", caller, min_rows, len(df))
        return False
    return True


def _now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _make_signal(
    pattern_name: str,
    symbol: str,
    confidence: float,
    entry_price: float,
    stop_price: float,
    metadata: Optional[dict] = None,
) -> dict:
    return {
        "pattern_name": pattern_name,
        "symbol": symbol,
        "confidence": round(float(confidence), 4),
        "entry_price": round(float(entry_price), 4),
        "stop_price": round(float(stop_price), 4),
        "detected_at": _now_iso(),
        "metadata": metadata or {},
    }


# ----- base class ----------------------------------------------------------- #
class BaseSetup(ABC):
    """Abstract base for all playbook setups."""

    name: str = "BaseSetup"
    description: str = ""

    @abstractmethod
    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        """
        Scan *df* for this pattern.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV data, oldest row first.
        symbol : str
            Ticker symbol (used only for labelling the returned signal dict).

        Returns
        -------
        dict or None
            Signal dict if the pattern is detected, else None.
        """


# ----- EpisodicPivot -------------------------------------------------------- #
class EpisodicPivot(BaseSetup):
    """
    Episodic Pivot (gap-up on highest volume of year).

    Criteria
    --------
    * Gap-up > 4 % vs previous close on the most recent bar.
    * Current bar's volume is the highest in the trailing 252 bars (≈ 1 year).

    Entry  : buy stop above the high of the opening range (approx. session high).
    Stop   : low of the gap-up day.
    """

    name = "EpisodicPivot"
    description = "Gap up >4% on highest volume of year; buy break of open-range high."

    GAP_MIN = 0.04          # minimum gap-up percentage
    MIN_ROWS = 30           # minimum history needed

    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        if not _validate(df, self.MIN_ROWS, self.name):
            return None

        today = df.iloc[-1]
        prev = df.iloc[-2]

        gap_pct = (float(today["Open"]) - float(prev["Close"])) / float(prev["Close"])
        if gap_pct < self.GAP_MIN:
            return None

        # Highest volume of available history (up to 252 bars)
        lookback = df["Volume"].iloc[max(0, len(df) - 252):]
        if float(today["Volume"]) < float(lookback.max()):
            return None

        entry = float(today["High"])   # break above session high
        stop = float(today["Low"])

        return _make_signal(
            self.name, symbol, confidence=0.80,
            entry_price=entry, stop_price=stop,
            metadata={"gap_pct": round(gap_pct, 4), "volume": int(today["Volume"])},
        )


# ----- MomentumBurst -------------------------------------------------------- #
class MomentumBurst(BaseSetup):
    """
    Momentum Burst (breakout after tight low-volume consolidation in uptrend).

    Criteria
    --------
    * Prior uptrend: 20-day return > 5 %.
    * Last 2–3 bars form a tight range: H-L spread < 2 % of price each day,
      and volume below 20-day average.
    * Current bar: closes above the consolidation range high (breakout)
      on above-average volume.
    """

    name = "MomentumBurst"
    description = "Breakout from 2-3 day tight low-vol consolidation in an uptrend."

    TREND_MIN = 0.05        # minimum 20-day return for uptrend
    TIGHT_RANGE = 0.02      # max H-L / price during consolidation
    CONSOL_BARS = 3         # consolidation window
    MIN_ROWS = 25

    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        if not _validate(df, self.MIN_ROWS, self.name):
            return None

        # Prior uptrend check
        trend_ret = (float(df["Close"].iloc[-4]) - float(df["Close"].iloc[-24])) / float(df["Close"].iloc[-24])
        if trend_ret < self.TREND_MIN:
            return None

        # Consolidation window: bars -4 through -2 (exclusive of today)
        consol = df.iloc[-(self.CONSOL_BARS + 1):-1]
        avg_vol = float(df["Volume"].iloc[-21:-1].mean())

        for _, bar in consol.iterrows():
            spread = (float(bar["High"]) - float(bar["Low"])) / float(bar["Close"])
            if spread > self.TIGHT_RANGE:
                return None
            if float(bar["Volume"]) > avg_vol:
                return None

        # Today must break above the consolidation high on high volume
        consol_high = float(consol["High"].max())
        today = df.iloc[-1]
        if float(today["Close"]) <= consol_high:
            return None
        if float(today["Volume"]) <= avg_vol:
            return None

        entry = float(today["High"]) * 1.001   # slight buffer above today's high
        stop = float(consol["Low"].min())

        return _make_signal(
            self.name, symbol, confidence=0.72,
            entry_price=entry, stop_price=stop,
            metadata={"trend_ret": round(trend_ret, 4), "consol_high": round(consol_high, 4)},
        )


# ----- ElephantBar ---------------------------------------------------------- #
class ElephantBar(BaseSetup):
    """
    Elephant Bar (massive green candle off 20-day MA).

    Criteria
    --------
    * Close > Open (green candle).
    * Bar range (H – L) is notably larger than the average of the prior 20 bars
      (by default > 2×).
    * Close is within 3 % of the 20-day SMA (bar originates near the MA).

    Entry  : above the high of the elephant bar.
    Stop   : below the low of the elephant bar.
    """

    name = "ElephantBar"
    description = "Massive green candle off 20-day MA, notably larger than prior 20 bars."

    SIZE_MULT = 2.0     # today's range must be > SIZE_MULT × avg prior range
    MA_PROXIMITY = 0.03 # low must be within 3 % of 20-SMA
    MIN_ROWS = 22

    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        if not _validate(df, self.MIN_ROWS, self.name):
            return None

        today = df.iloc[-1]
        prior = df.iloc[-21:-1]

        # Green candle
        if float(today["Close"]) <= float(today["Open"]):
            return None

        today_range = float(today["High"]) - float(today["Low"])
        prior_ranges = prior["High"].values.astype(float) - prior["Low"].values.astype(float)
        avg_prior_range = float(np.mean(prior_ranges))

        if avg_prior_range <= 0 or today_range < self.SIZE_MULT * avg_prior_range:
            return None

        sma20 = float(prior["Close"].mean())
        proximity = abs(float(today["Low"]) - sma20) / sma20
        if proximity > self.MA_PROXIMITY:
            return None

        entry = float(today["High"]) * 1.001
        stop = float(today["Low"])

        return _make_signal(
            self.name, symbol, confidence=0.75,
            entry_price=entry, stop_price=stop,
            metadata={
                "today_range": round(today_range, 4),
                "avg_prior_range": round(avg_prior_range, 4),
                "sma20": round(sma20, 4),
            },
        )


# ----- VCP ------------------------------------------------------------------ #
class VCP(BaseSetup):
    """
    Volatility Contraction Pattern (tightening waves).

    Criteria
    --------
    * Identifies at least 3 pullback waves within the last 60 bars.
    * Each successive wave is smaller than the previous by ≥ 30 %.
      Example: 15 % → 8 % → 3 % drops.
    * Volume trends lower through the contractions.
    * Current price is within 3 % of the peak of the tightest wave (the pivot).

    Entry  : buy stop above the tightest pivot high.
    Stop   : below the most recent consolidation low.
    """

    name = "VCP"
    description = "Volatility contraction: tightening waves e.g. 15%→8%→3%; buy above pivot."

    MIN_WAVES = 3
    CONTRACTION_RATIO = 0.70   # each wave ≤ 70 % of the previous wave's depth
    PIVOT_PROXIMITY = 0.03     # price within 3 % of tightest pivot high
    LOOKBACK = 60
    MIN_ROWS = 65

    def _find_waves(self, close: np.ndarray) -> list:
        """
        Simple wave detector: find local maxima/minima and measure pullback %.
        Returns a list of (peak_price, trough_price, drawdown_pct).
        """
        waves = []
        n = len(close)
        in_drawdown = False
        peak = close[0]
        trough = close[0]

        for i in range(1, n):
            if close[i] > peak:
                if in_drawdown and peak > 0 and trough < peak:
                    dd = (peak - trough) / peak
                    waves.append((float(peak), float(trough), float(dd)))
                peak = close[i]
                trough = close[i]
                in_drawdown = False
            elif close[i] < trough:
                trough = close[i]
                in_drawdown = True

        return waves

    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        if not _validate(df, self.MIN_ROWS, self.name):
            return None

        window = df.iloc[-self.LOOKBACK:]
        close = window["Close"].values.astype(float)
        waves = self._find_waves(close)

        if len(waves) < self.MIN_WAVES:
            return None

        # Check that successive waves are contracting
        for i in range(1, len(waves)):
            if waves[i][2] > waves[i - 1][2] * self.CONTRACTION_RATIO:
                return None   # wave expanded — not a VCP

        # Tightest wave pivot high
        tightest = waves[-1]
        pivot_high = float(tightest[0])
        current_price = float(df["Close"].iloc[-1])

        if abs(current_price - pivot_high) / pivot_high > self.PIVOT_PROXIMITY:
            return None

        entry = pivot_high * 1.001
        stop = float(tightest[1])   # trough of tightest wave

        return _make_signal(
            self.name, symbol, confidence=0.78,
            entry_price=entry, stop_price=stop,
            metadata={
                "num_waves": len(waves),
                "wave_depths": [round(w[2], 4) for w in waves[-3:]],
                "pivot_high": round(pivot_high, 4),
            },
        )


# ----- HighTightFlag -------------------------------------------------------- #
class HighTightFlag(BaseSetup):
    """
    High Tight Flag (doubled in < 8 weeks, then flat consolidation).

    Criteria
    --------
    * Stock at least doubled within the prior 40 trading days.
    * Last 3–5 days form a flat flag: daily range < 20 % of the prior move.
    * Flag consolidation < 20 % retrace of the prior leg.

    Entry  : breakout above the flag high.
    Stop   : flag low.
    """

    name = "HighTightFlag"
    description = "Doubled in <8 weeks, 3-5 day flat consolidation <20% retrace."

    DOUBLE_BARS = 40        # 8 trading weeks
    FLAG_BARS_MIN = 3
    FLAG_BARS_MAX = 5
    RETRACE_MAX = 0.20      # flag retrace must be < 20 % of prior leg
    MIN_ROWS = 46           # 40 base + 5 flag + buffer

    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        if not _validate(df, self.MIN_ROWS, self.name):
            return None

        # Check for a double in the prior 40 bars before the flag
        flag_end = -1          # today is the end of the flag
        flag_start = -(self.FLAG_BARS_MAX + 1)
        base_start = -(self.DOUBLE_BARS + self.FLAG_BARS_MAX + 1)

        base_low = float(df["Close"].iloc[base_start:flag_start].min())
        flag_high = float(df["High"].iloc[flag_start:].max())
        flag_low = float(df["Low"].iloc[flag_start:].min())

        if base_low <= 0:
            return None

        # Must have (at least) doubled from base low to flag high
        if (flag_high - base_low) / base_low < 1.0:
            return None

        prior_leg = flag_high - base_low
        retrace = (flag_high - flag_low) / prior_leg if prior_leg > 0 else 1.0

        if retrace > self.RETRACE_MAX:
            return None

        # Today must be a breakout above flag high on elevated volume
        today = df.iloc[-1]
        avg_vol = float(df["Volume"].iloc[-21:-1].mean())

        if float(today["Close"]) <= flag_high:
            return None
        if avg_vol > 0 and float(today["Volume"]) < 3.0 * avg_vol:
            return None

        entry = flag_high * 1.001
        stop = flag_low

        return _make_signal(
            self.name, symbol, confidence=0.82,
            entry_price=entry, stop_price=stop,
            metadata={
                "base_low": round(base_low, 4),
                "flag_high": round(flag_high, 4),
                "retrace_pct": round(retrace, 4),
            },
        )


# ----- InsideBar212 --------------------------------------------------------- #
class InsideBar212(BaseSetup):
    """
    Inside Bar 2-1-2 (directional bar → inside bar → continuation).

    Criteria
    --------
    * Bar N-1: directional bar — closes up > 1 % from its open (bullish) and
      from prior close.
    * Bar N (today): inside bar — High < Bar_(N-1).High AND Low > Bar_(N-1).Low.

    Entry  : buy stop just above the inside bar high.
    Stop   : just below the inside bar low.
    """

    name = "InsideBar212"
    description = "Directional bar + inside bar contained within prior range; buy above IB high."

    DIRECTIONAL_MOVE = 0.01   # bar N-1 must close up > 1 % from open
    MIN_ROWS = 3

    def detect(self, df: pd.DataFrame, symbol: str) -> Optional[dict]:
        if not _validate(df, self.MIN_ROWS, self.name):
            return None

        bar_n2 = df.iloc[-3]   # two bars ago
        bar_n1 = df.iloc[-2]   # directional bar
        bar_n0 = df.iloc[-1]   # inside bar (today)

        # Bar N-1: directional (bullish)
        n1_move_from_open = (float(bar_n1["Close"]) - float(bar_n1["Open"])) / float(bar_n1["Open"])
        n1_move_from_prev = (float(bar_n1["Close"]) - float(bar_n2["Close"])) / float(bar_n2["Close"])

        if n1_move_from_open < self.DIRECTIONAL_MOVE:
            return None
        if n1_move_from_prev < self.DIRECTIONAL_MOVE:
            return None

        # Bar N: inside bar
        if float(bar_n0["High"]) >= float(bar_n1["High"]):
            return None
        if float(bar_n0["Low"]) <= float(bar_n1["Low"]):
            return None

        entry = float(bar_n0["High"]) * 1.001
        stop = float(bar_n0["Low"]) * 0.999

        return _make_signal(
            self.name, symbol, confidence=0.68,
            entry_price=entry, stop_price=stop,
            metadata={
                "n1_move_pct": round(n1_move_from_open, 4),
                "inside_bar_range": round(float(bar_n0["High"]) - float(bar_n0["Low"]), 4),
            },
        )


# ----- Registry ------------------------------------------------------------- #
# All registered detectors are instantiated once at import time.
SIGNAL_REGISTRY: list = [
    EpisodicPivot(),
    MomentumBurst(),
    ElephantBar(),
    VCP(),
    HighTightFlag(),
    InsideBar212(),
]


def scan_symbol(df: pd.DataFrame, symbol: str) -> list:
    """
    Run all registered detectors against *df* and return every signal found.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data for *symbol*, oldest row first.
    symbol : str
        Ticker label applied to each returned signal dict.

    Returns
    -------
    list[dict]
        Zero or more signal dicts (one per triggered detector).
    """
    signals = []
    for detector in SIGNAL_REGISTRY:
        try:
            result = detector.detect(df, symbol)
            if result is not None:
                signals.append(result)
        except Exception as exc:
            logger.warning("[SignalCatalog] %s.detect(%s) raised: %s", detector.name, symbol, exc)
    return signals
