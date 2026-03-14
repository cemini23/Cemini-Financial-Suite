"""
Feature normalization for the RL observation space.
"""
from __future__ import annotations

import polars as pl

from shared.feature_engine.config import NormMethod


def normalize_feature(
    series: pl.Series,
    method: NormMethod,
    min_val: float = 0.0,
    max_val: float = 100.0,
    clip_sigma: float = 3.0,
) -> pl.Series:
    """Normalize a feature series according to the specified method."""
    name = series.name

    if method == NormMethod.LOG_RETURN:
        result = series.cast(pl.Float64)
        result = result.map_elements(
            lambda x: x if x is not None and (x == x) and abs(x) < 1e10 else 0.0,
            return_dtype=pl.Float64,
        )
        return result.alias(name)

    if method == NormMethod.MINMAX:
        rng = max_val - min_val
        if rng == 0.0:
            return pl.Series(name, [0.0] * len(series))
        result = (series.cast(pl.Float64) - min_val) / rng
        return result.clip(0.0, 1.0).alias(name)

    if method == NormMethod.ZSCORE_CLIP:
        s = series.cast(pl.Float64)
        mean_val = s.mean()
        std_val = s.std()
        if std_val is None or std_val == 0.0:
            return pl.Series(name, [0.0] * len(series))
        z = (s - mean_val) / std_val
        return z.clip(-clip_sigma, clip_sigma).alias(name)

    if method == NormMethod.PASSTHROUGH:
        return series.cast(pl.Float64).alias(name)

    # ONEHOT handled in feature_matrix assembly
    return series.cast(pl.Float64).alias(name)


def fill_nulls(series: pl.Series, fill_value: float = 0.0) -> pl.Series:
    """Fill null/NaN values."""
    return series.fill_null(fill_value).fill_nan(fill_value)
