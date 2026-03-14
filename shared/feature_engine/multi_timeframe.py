"""
Multi-timeframe feature alignment using Polars group_by_dynamic + join_asof.
"""
from __future__ import annotations

import polars as pl


def aggregate_timeframe(
    ticks_1m: pl.DataFrame,
    minutes: int,
    label: str,
) -> pl.DataFrame:
    """Aggregate 1-min OHLCV bars into a higher timeframe."""
    return (
        ticks_1m
        .sort("timestamp")
        .group_by_dynamic("timestamp", every=f"{minutes}m")
        .agg([
            pl.col("open").first().alias(f"open_{label}"),
            pl.col("high").max().alias(f"high_{label}"),
            pl.col("low").min().alias(f"low_{label}"),
            pl.col("close").last().alias(f"close_{label}"),
            pl.col("volume").sum().alias(f"volume_{label}"),
        ])
        .sort("timestamp")
    )


def build_multi_timeframe(
    ticks_1m: pl.DataFrame,
    timeframes: dict[str, int],
) -> pl.DataFrame:
    """
    Build multi-timeframe features by aggregating 1-min bars
    and aligning back to the 1-min timeline via backward join_asof.

    No future data leakage: join_asof with strategy="backward" only
    looks at candles whose start timestamp <= the current 1-min bar.
    """
    result = ticks_1m.sort("timestamp")
    for label, minutes in timeframes.items():
        if minutes <= 1:
            continue
        agg = aggregate_timeframe(ticks_1m, minutes, label)
        result = result.join_asof(agg, on="timestamp", strategy="backward")
    return result
