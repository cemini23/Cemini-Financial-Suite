"""
Technical indicator computations using pure Polars expressions.
RSI uses Wilder's SMMA (alpha=1/period) — NOT simple SMA.
"""
from __future__ import annotations

import polars as pl


def rsi_wilder(df: pl.DataFrame, column: str = "close", period: int = 14) -> pl.Series:
    """
    RSI using Wilder's Smoothed Moving Average (SMMA).
    alpha = 1/period  ↔  span = 2*period - 1 in ewm notation.
    This is the industry standard (Wilder 1978, matches TradingView/pandas-ta).
    """
    delta = df[column].diff()
    gain = delta.map_elements(lambda x: x if x is not None and x > 0 else 0.0, return_dtype=pl.Float64)
    loss = delta.map_elements(lambda x: -x if x is not None and x < 0 else 0.0, return_dtype=pl.Float64)
    span = 2 * period - 1
    avg_gain = gain.ewm_mean(span=span, adjust=False)
    avg_loss = loss.ewm_mean(span=span, adjust=False)
    rs = avg_gain / avg_loss.map_elements(lambda x: x if x != 0.0 else 1e-10, return_dtype=pl.Float64)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.alias("rsi_14")


def macd(
    df: pl.DataFrame,
    column: str = "close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pl.DataFrame:
    """MACD line, signal line, and histogram."""
    prices = df[column].cast(pl.Float64)
    ema_fast = prices.ewm_mean(span=fast, adjust=False)
    ema_slow = prices.ewm_mean(span=slow, adjust=False)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm_mean(span=signal, adjust=False)
    histogram = macd_line - signal_line
    return df.with_columns([
        macd_line.alias("macd_line"),
        signal_line.alias("macd_signal"),
        histogram.alias("macd_histogram"),
    ])


def bollinger_bands(
    df: pl.DataFrame,
    column: str = "close",
    period: int = 20,
    std_dev: float = 2.0,
) -> pl.DataFrame:
    """Bollinger Bands: middle, upper, lower, and width (% of middle)."""
    prices = df[column].cast(pl.Float64)
    middle = prices.rolling_mean(window_size=period)
    std = prices.rolling_std(window_size=period)
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    width = (upper - lower) / middle.map_elements(
        lambda x: x if x is not None and x != 0.0 else 1.0, return_dtype=pl.Float64
    )
    return df.with_columns([
        middle.alias("bb_middle"),
        upper.alias("bb_upper"),
        lower.alias("bb_lower"),
        width.alias("bb_width"),
    ])


def atr(df: pl.DataFrame, period: int = 14) -> pl.Series:
    """Average True Range (14)."""
    high = df["high"].cast(pl.Float64)
    low = df["low"].cast(pl.Float64)
    close = df["close"].cast(pl.Float64)
    prev_close = close.shift(1)
    tr = pl.Series([
        max(h - ln, abs(h - pc) if pc is not None else h - ln, abs(ln - pc) if pc is not None else h - ln)
        for h, ln, pc in zip(high.to_list(), low.to_list(), prev_close.to_list(), strict=False)
    ])
    atr_series = tr.ewm_mean(span=2 * period - 1, adjust=False)
    return atr_series.alias("atr_14")


def mfi(df: pl.DataFrame, period: int = 14) -> pl.Series:
    """Money Flow Index (14). Requires high, low, close, volume columns."""
    high = df["high"].cast(pl.Float64)
    low = df["low"].cast(pl.Float64)
    close = df["close"].cast(pl.Float64)
    volume = df["volume"].cast(pl.Float64)
    typical_price = (high + low + close) / 3.0
    raw_money_flow = typical_price * volume
    tp_diff = typical_price.diff()

    pos_flow: list[float] = []
    neg_flow: list[float] = []
    tp_list = tp_diff.to_list()
    rmf_list = raw_money_flow.to_list()
    for i, diff in enumerate(tp_list):
        rmf_val = rmf_list[i] if rmf_list[i] is not None else 0.0
        if diff is None or diff >= 0:
            pos_flow.append(rmf_val)
            neg_flow.append(0.0)
        else:
            pos_flow.append(0.0)
            neg_flow.append(rmf_val)

    pos_series = pl.Series(pos_flow)
    neg_series = pl.Series(neg_flow)
    pos_sum = pos_series.rolling_sum(window_size=period)
    neg_sum = neg_series.rolling_sum(window_size=period)
    mfr = pos_sum / neg_sum.map_elements(lambda x: x if x is not None and x != 0.0 else 1e-10, return_dtype=pl.Float64)
    mfi_series = 100.0 - (100.0 / (1.0 + mfr))
    return mfi_series.alias("mfi_14")


def log_returns(df: pl.DataFrame, column: str = "close", periods: list[int] | None = None) -> pl.DataFrame:
    """Compute log returns for multiple lookback periods."""
    if periods is None:
        periods = [1, 5, 60]
    prices = df[column].cast(pl.Float64)
    result = df
    for p in periods:
        lr = (prices / prices.shift(p)).log()
        label = f"log_return_{p}m" if p < 60 else "log_return_1h"
        result = result.with_columns(lr.alias(label))
    return result


def volume_zscore(df: pl.DataFrame, period: int = 20) -> pl.Series:
    """Volume Z-score vs rolling mean."""
    vol = df["volume"].cast(pl.Float64)
    mean = vol.rolling_mean(window_size=period)
    std = vol.rolling_std(window_size=period)
    z = (vol - mean) / std.map_elements(lambda x: x if x is not None and x != 0.0 else 1.0, return_dtype=pl.Float64)
    return z.alias("volume_zscore")


def add_all_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Add all technical indicators to a tick DataFrame."""
    df = df.with_columns(rsi_wilder(df).alias("rsi_14"))
    df = macd(df)
    df = bollinger_bands(df)
    df = df.with_columns(atr(df).alias("atr_14"))
    df = df.with_columns(mfi(df).alias("mfi_14"))
    df = log_returns(df, periods=[1, 5, 60])
    df = df.with_columns(volume_zscore(df).alias("volume_zscore"))
    return df
