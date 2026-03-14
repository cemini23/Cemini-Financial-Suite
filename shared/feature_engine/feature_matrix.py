"""
Assembles the final normalized feature matrix for TorchRL consumption.
"""
from __future__ import annotations

import logging

import polars as pl

from shared.feature_engine.config import ALL_FEATURES, FEATURE_VECTOR_DIM, NormMethod, TIMEFRAMES
from shared.feature_engine import data_loader, indicators, multi_timeframe, normalizer

logger = logging.getLogger("cemini.feature_engine.feature_matrix")


def build_feature_matrix(
    ticker: str,
    start: str,
    end: str,
) -> pl.DataFrame:
    """
    Build the complete normalized feature matrix for a single ticker.
    Returns a Polars DataFrame: one row per timestamp, one column per feature.
    Ready for to_numpy() → TorchRL.
    """
    ticks = data_loader.load_market_ticks(ticker, start, end)
    if ticks.is_empty():
        logger.warning("No tick data for %s [%s, %s)", ticker, start, end)
        return pl.DataFrame()

    mtf = multi_timeframe.build_multi_timeframe(ticks, TIMEFRAMES)
    mtf = indicators.add_all_indicators(mtf)

    try:
        macro = data_loader.load_macro_logs(start, end)
        if not macro.is_empty():
            mtf = mtf.join_asof(macro.sort("timestamp"), on="timestamp", strategy="backward")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load macro_logs: %s", exc)

    try:
        regime_df = data_loader.load_playbook_regime(start, end)
        if not regime_df.is_empty():
            mtf = mtf.join_asof(regime_df.sort("timestamp"), on="timestamp", strategy="backward")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load playbook_logs: %s", exc)

    if "regime" in mtf.columns:
        mtf = mtf.with_columns([
            (pl.col("regime") == "GREEN").cast(pl.Float64).alias("regime_green"),
            (pl.col("regime") == "YELLOW").cast(pl.Float64).alias("regime_yellow"),
            (pl.col("regime") == "RED").cast(pl.Float64).alias("regime_red"),
        ])
    else:
        mtf = mtf.with_columns([
            pl.lit(0.0).alias("regime_green"),
            pl.lit(0.0).alias("regime_yellow"),
            pl.lit(0.0).alias("regime_red"),
        ])

    if "fear_greed_index" in mtf.columns:
        mtf = mtf.rename({"fear_greed_index": "fgi_normalized"})
    elif "fgi_normalized" not in mtf.columns:
        mtf = mtf.with_columns(pl.lit(0.0).alias("fgi_normalized"))

    for col in ["finbert_sentiment", "treasury_10y", "yield_curve_spread", "credit_spread"]:
        if col not in mtf.columns:
            mtf = mtf.with_columns(pl.lit(0.0).alias(col))

    for feat in ALL_FEATURES:
        if feat.norm_method == NormMethod.ONEHOT:
            continue
        if feat.name not in mtf.columns:
            mtf = mtf.with_columns(pl.lit(0.0).alias(feat.name))
            continue
        normalized = normalizer.normalize_feature(mtf[feat.name], feat.norm_method)
        normalized = normalizer.fill_nulls(normalized)
        mtf = mtf.with_columns(normalized.alias(feat.name))

    feature_cols = [f.name for f in ALL_FEATURES]
    available = [c for c in feature_cols if c in mtf.columns]
    result = mtf.select(["timestamp"] + available)
    result = result.drop_nulls()
    logger.info(
        "Feature matrix built for %s: %d rows × %d features",
        ticker, len(result), FEATURE_VECTOR_DIM,
    )
    return result


def to_numpy(df: pl.DataFrame):  # type: ignore[return]
    """Convert feature matrix to NumPy array for TorchRL. Returns np.ndarray."""
    import numpy as np  # noqa: PLC0415

    feature_cols = [c for c in df.columns if c != "timestamp"]
    arr = df.select(feature_cols).to_numpy()
    return arr.astype(np.float32)
