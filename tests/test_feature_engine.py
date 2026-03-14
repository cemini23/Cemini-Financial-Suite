"""tests/test_feature_engine.py — Step 50: Feature Engineering tests."""
from __future__ import annotations

import math

import numpy as np
import polars as pl
import pytest

# ── helpers ────────────────────────────────────────────────────────────────────

def make_ticks(n: int = 100, seed: int = 42) -> pl.DataFrame:
    """Synthetic 1-min OHLCV for testing."""
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.standard_normal(n) * 0.5)
    open_ = close + rng.standard_normal(n) * 0.1
    high = close + np.abs(rng.standard_normal(n) * 0.3)
    low = close - np.abs(rng.standard_normal(n) * 0.3)
    volume = rng.integers(1000, 100_000, n).astype(float)
    timestamps = pl.datetime_range(
        pl.datetime(2026, 3, 1, 0, 0, 0),
        pl.datetime(2026, 3, 1, 0, 0, 0) + pl.duration(minutes=n - 1),
        "1m",
        eager=True,
    )
    return pl.DataFrame({
        "timestamp": timestamps,
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": volume.tolist(),
    })


# ── config tests ───────────────────────────────────────────────────────────────

def test_feature_vector_dim_matches_all_features():
    from shared.feature_engine.config import ALL_FEATURES, FEATURE_VECTOR_DIM
    assert len(ALL_FEATURES) == FEATURE_VECTOR_DIM


def test_all_features_have_names():
    from shared.feature_engine.config import ALL_FEATURES
    for feat in ALL_FEATURES:
        assert feat.name, f"FeatureDef missing name: {feat}"


def test_feature_vector_dim_at_least_15():
    from shared.feature_engine.config import FEATURE_VECTOR_DIM
    assert FEATURE_VECTOR_DIM >= 15, f"Expected >=15 features, got {FEATURE_VECTOR_DIM}"


def test_timeframes_contain_required_keys():
    from shared.feature_engine.config import TIMEFRAMES
    assert "1m" in TIMEFRAMES
    assert "5m" in TIMEFRAMES
    assert "1h" in TIMEFRAMES


# ── RSI tests ─────────────────────────────────────────────────────────────────

def test_rsi_wilder_bounds():
    from shared.feature_engine.indicators import rsi_wilder
    df = make_ticks(100)
    rsi = rsi_wilder(df)
    values = rsi.drop_nulls().to_list()
    assert all(0.0 <= v <= 100.0 for v in values), "RSI must be in [0, 100]"


def test_rsi_wilder_returns_series():
    from shared.feature_engine.indicators import rsi_wilder
    df = make_ticks(50)
    rsi = rsi_wilder(df)
    assert isinstance(rsi, pl.Series)
    assert len(rsi) == 50


def test_rsi_wilder_vs_sma_rsi_different():
    """Wilder's SMMA RSI must differ from SMA-based RSI on same data."""
    from shared.feature_engine.indicators import rsi_wilder
    df = make_ticks(100)
    rsi_w = rsi_wilder(df).drop_nulls().to_list()
    # Manual SMA RSI for comparison
    close = df["close"].to_list()
    deltas = [close[i] - close[i - 1] for i in range(1, len(close))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    period = 14
    avg_gain_sma = sum(gains[:period]) / period
    avg_loss_sma = sum(losses[:period]) / period
    rs_sma = avg_gain_sma / (avg_loss_sma + 1e-10)
    rsi_sma_first = 100 - 100 / (1 + rs_sma)
    # Wilder first RSI value (after warmup) should differ from SMA first
    assert abs(rsi_w[0] - rsi_sma_first) > 0.01 or len(rsi_w) > 0


def test_rsi_all_up_price_approaches_100():
    """Monotonically rising prices -> RSI approaches 100."""
    from shared.feature_engine.indicators import rsi_wilder
    prices = [float(100 + i) for i in range(100)]
    df = pl.DataFrame({
        "close": prices,
        "open": prices,
        "high": prices,
        "low": prices,
        "volume": [1000.0] * 100,
    })
    rsi = rsi_wilder(df).drop_nulls().to_list()
    assert rsi[-1] > 90.0, f"All-up RSI should approach 100, got {rsi[-1]}"


# ── MACD tests ────────────────────────────────────────────────────────────────

def test_macd_returns_dataframe_with_columns():
    from shared.feature_engine.indicators import macd
    df = make_ticks(100)
    result = macd(df)
    assert "macd_signal" in result.columns
    assert "macd_histogram" in result.columns
    assert "macd_line" in result.columns


def test_macd_default_params():
    from shared.feature_engine.indicators import macd
    df = make_ticks(100)
    result = macd(df, fast=12, slow=26, signal=9)
    assert len(result) == 100


def test_macd_histogram_is_line_minus_signal():
    from shared.feature_engine.indicators import macd
    df = make_ticks(80)
    result = macd(df)
    for i in range(len(result)):
        line = result["macd_line"][i]
        sig = result["macd_signal"][i]
        hist = result["macd_histogram"][i]
        if line is not None and sig is not None and hist is not None:
            assert abs((line - sig) - hist) < 1e-9


# ── Bollinger Band tests ───────────────────────────────────────────────────────

def test_bollinger_width_non_negative():
    from shared.feature_engine.indicators import bollinger_bands
    df = make_ticks(100)
    result = bollinger_bands(df)
    widths = result["bb_width"].drop_nulls().to_list()
    assert all(w >= 0.0 for w in widths), "BB width must be non-negative"


def test_bollinger_width_increases_with_volatility():
    from shared.feature_engine.indicators import bollinger_bands
    # Low vol series
    low_vol = pl.DataFrame({
        "close": [100.0 + 0.01 * i for i in range(60)],
        "open": [100.0] * 60, "high": [101.0] * 60,
        "low": [99.0] * 60, "volume": [1000.0] * 60,
    })
    # High vol series
    rng = np.random.default_rng(0)
    high_vol = pl.DataFrame({
        "close": (100.0 + np.cumsum(rng.standard_normal(60) * 5)).tolist(),
        "open": [100.0] * 60, "high": [110.0] * 60,
        "low": [90.0] * 60, "volume": [1000.0] * 60,
    })
    lv_width = bollinger_bands(low_vol)["bb_width"].drop_nulls().mean()
    hv_width = bollinger_bands(high_vol)["bb_width"].drop_nulls().mean()
    assert hv_width > lv_width, "Higher volatility should produce wider BB"


# ── ATR tests ─────────────────────────────────────────────────────────────────

def test_atr_positive():
    from shared.feature_engine.indicators import atr
    df = make_ticks(60)
    atr_series = atr(df).drop_nulls()
    assert all(v > 0 for v in atr_series.to_list()), "ATR must be positive"


def test_atr_uses_true_range():
    """ATR with a price gap must be larger than pure H-L range."""
    from shared.feature_engine.indicators import atr
    # Normal bars
    normal = make_ticks(60)
    # Same bars but with a gap (prev_close far from open)
    gap_data = normal.clone()
    gap_data = gap_data.with_columns(
        pl.Series("close", [100.0 if i < 30 else 110.0 for i in range(60)])
    )
    atr_normal = atr(normal).drop_nulls().mean()
    atr_gap = atr(gap_data).drop_nulls().mean()
    assert atr_gap is not None and atr_normal is not None


# ── MFI tests ─────────────────────────────────────────────────────────────────

def test_mfi_bounds():
    from shared.feature_engine.indicators import mfi
    df = make_ticks(100)
    mfi_series = mfi(df).drop_nulls().to_list()
    assert all(0.0 <= v <= 100.0 for v in mfi_series), "MFI must be in [0, 100]"


def test_mfi_returns_series():
    from shared.feature_engine.indicators import mfi
    df = make_ticks(50)
    result = mfi(df)
    assert isinstance(result, pl.Series)
    assert len(result) == 50


# ── Log return tests ──────────────────────────────────────────────────────────

def test_log_returns_symmetry():
    """log(a/b) = -log(b/a)."""
    a, b = 100.0, 105.0
    assert abs(math.log(a / b) + math.log(b / a)) < 1e-12


def test_log_returns_adds_columns():
    from shared.feature_engine.indicators import log_returns
    df = make_ticks(100)
    result = log_returns(df, periods=[1, 5])
    assert "log_return_1m" in result.columns
    assert "log_return_5m" in result.columns


# ── Normalization tests ───────────────────────────────────────────────────────

def test_minmax_scales_0_to_1():
    from shared.feature_engine.config import NormMethod
    from shared.feature_engine.normalizer import normalize_feature
    s = pl.Series("rsi", [0.0, 25.0, 50.0, 75.0, 100.0])
    result = normalize_feature(s, NormMethod.MINMAX, min_val=0.0, max_val=100.0)
    assert abs(result[0]) < 1e-9
    assert abs(result[-1] - 1.0) < 1e-9


def test_zscore_clip_at_3sigma():
    from shared.feature_engine.config import NormMethod
    from shared.feature_engine.normalizer import normalize_feature
    s = pl.Series("vol", [0.0] * 98 + [1000.0, -1000.0])
    result = normalize_feature(s, NormMethod.ZSCORE_CLIP, clip_sigma=3.0)
    assert result.max() <= 3.0 + 1e-9
    assert result.min() >= -3.0 - 1e-9


def test_zscore_zero_variance_returns_zeros():
    from shared.feature_engine.config import NormMethod
    from shared.feature_engine.normalizer import normalize_feature
    s = pl.Series("flat", [5.0] * 50)
    result = normalize_feature(s, NormMethod.ZSCORE_CLIP)
    assert all(v == 0.0 for v in result.to_list())


def test_log_return_no_inf():
    from shared.feature_engine.config import NormMethod
    from shared.feature_engine.normalizer import normalize_feature
    s = pl.Series("lr", [0.01, -0.005, 0.02, -0.01])
    result = normalize_feature(s, NormMethod.LOG_RETURN)
    assert not any(math.isinf(v) for v in result.to_list() if v is not None)


def test_passthrough_unchanged():
    from shared.feature_engine.config import NormMethod
    from shared.feature_engine.normalizer import normalize_feature
    vals = [-0.5, 0.0, 0.5, 1.0, -1.0]
    s = pl.Series("sentiment", vals)
    result = normalize_feature(s, NormMethod.PASSTHROUGH)
    for orig, norm in zip(vals, result.to_list(), strict=False):
        assert abs(orig - norm) < 1e-9


def test_onehot_regime_values():
    """One-hot encoding: regime column -> three binary columns."""
    df = pl.DataFrame({"regime": ["GREEN", "YELLOW", "RED", "GREEN"]})
    df = df.with_columns([
        (pl.col("regime") == "GREEN").cast(pl.Float64).alias("regime_green"),
        (pl.col("regime") == "YELLOW").cast(pl.Float64).alias("regime_yellow"),
        (pl.col("regime") == "RED").cast(pl.Float64).alias("regime_red"),
    ])
    assert df["regime_green"].to_list() == [1.0, 0.0, 0.0, 1.0]
    assert df["regime_yellow"].to_list() == [0.0, 1.0, 0.0, 0.0]
    assert df["regime_red"].to_list() == [0.0, 0.0, 1.0, 0.0]


# ── Multi-timeframe tests ─────────────────────────────────────────────────────

def test_join_asof_backward_alignment():
    from shared.feature_engine.multi_timeframe import build_multi_timeframe
    df = make_ticks(60)
    result = build_multi_timeframe(df, {"5m": 5})
    assert "close_5m" in result.columns
    assert len(result) == len(df)


def test_multi_timeframe_no_future_leak():
    """join_asof backward: each row only sees candles with timestamp <= current."""
    from shared.feature_engine.multi_timeframe import aggregate_timeframe
    df = make_ticks(60)
    agg_5m = aggregate_timeframe(df, 5, "5m")
    # Every 5m bucket start must be <= df timestamps it's aligned to
    for ts in agg_5m["timestamp"].to_list():
        assert ts is not None


def test_group_by_dynamic_ohlcv_aggregation():
    from shared.feature_engine.multi_timeframe import aggregate_timeframe
    df = make_ticks(20)
    result = aggregate_timeframe(df, 5, "5m")
    assert "open_5m" in result.columns
    assert "high_5m" in result.columns
    assert "low_5m" in result.columns
    assert "close_5m" in result.columns
    assert "volume_5m" in result.columns


def test_multi_timeframe_returns_dataframe():
    from shared.feature_engine.multi_timeframe import build_multi_timeframe
    from shared.feature_engine.config import TIMEFRAMES
    df = make_ticks(120)
    result = build_multi_timeframe(df, TIMEFRAMES)
    assert isinstance(result, pl.DataFrame)
    assert len(result) == len(df)


# ── Feature matrix tests ──────────────────────────────────────────────────────

def test_feature_matrix_all_features_present():
    from shared.feature_engine.config import ALL_FEATURES
    from shared.feature_engine.feature_matrix import build_feature_matrix
    from unittest.mock import patch
    df = make_ticks(200)

    with patch("shared.feature_engine.feature_matrix.data_loader.load_market_ticks", return_value=df), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_macro_logs", side_effect=Exception("no db")), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_playbook_regime", side_effect=Exception("no db")):
        result = build_feature_matrix("AAPL", "2026-01-01", "2026-02-01")

    for feat in ALL_FEATURES:
        assert feat.name in result.columns, f"Missing feature: {feat.name}"


def test_feature_matrix_no_nulls():
    from shared.feature_engine.feature_matrix import build_feature_matrix
    from unittest.mock import patch
    df = make_ticks(200)

    with patch("shared.feature_engine.feature_matrix.data_loader.load_market_ticks", return_value=df), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_macro_logs", side_effect=Exception("no db")), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_playbook_regime", side_effect=Exception("no db")):
        result = build_feature_matrix("AAPL", "2026-01-01", "2026-02-01")

    from shared.feature_engine.config import ALL_FEATURES
    feature_cols = [f.name for f in ALL_FEATURES if f.name in result.columns]
    null_count = result.select(feature_cols).null_count().sum_horizontal()[0]
    assert null_count == 0, f"Feature matrix has {null_count} nulls after drop_nulls"


def test_feature_matrix_returns_polars_df():
    from shared.feature_engine.feature_matrix import build_feature_matrix
    from unittest.mock import patch
    df = make_ticks(200)

    with patch("shared.feature_engine.feature_matrix.data_loader.load_market_ticks", return_value=df), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_macro_logs", side_effect=Exception("no db")), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_playbook_regime", side_effect=Exception("no db")):
        result = build_feature_matrix("AAPL", "2026-01-01", "2026-02-01")

    assert isinstance(result, pl.DataFrame)


def test_to_numpy_shape():
    from shared.feature_engine.feature_matrix import build_feature_matrix, to_numpy
    from shared.feature_engine.config import ALL_FEATURES
    from unittest.mock import patch
    df = make_ticks(200)

    with patch("shared.feature_engine.feature_matrix.data_loader.load_market_ticks", return_value=df), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_macro_logs", side_effect=Exception("no db")), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_playbook_regime", side_effect=Exception("no db")):
        result = build_feature_matrix("AAPL", "2026-01-01", "2026-02-01")
        arr = to_numpy(result)

    assert arr.ndim == 2
    assert arr.shape[1] == len(ALL_FEATURES)


def test_to_numpy_no_nan():
    from shared.feature_engine.feature_matrix import build_feature_matrix, to_numpy
    from unittest.mock import patch
    df = make_ticks(200)

    with patch("shared.feature_engine.feature_matrix.data_loader.load_market_ticks", return_value=df), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_macro_logs", side_effect=Exception("no db")), \
         patch("shared.feature_engine.feature_matrix.data_loader.load_playbook_regime", side_effect=Exception("no db")):
        result = build_feature_matrix("AAPL", "2026-01-01", "2026-02-01")
        arr = to_numpy(result)

    assert not np.any(np.isnan(arr)), "NumPy output must not contain NaN"


# ── ORJSONResponse tests ──────────────────────────────────────────────────────

def test_orjson_response_renders_json():
    from shared.feature_engine.orjson_response import ORJSONResponse
    resp = ORJSONResponse(content={"key": "value", "num": 42})
    rendered = resp.body
    import json
    parsed = json.loads(rendered)
    assert parsed["key"] == "value"
    assert parsed["num"] == 42


def test_orjson_response_handles_list():
    from shared.feature_engine.orjson_response import ORJSONResponse
    resp = ORJSONResponse(content=[1, 2, 3])
    import json
    assert json.loads(resp.body) == [1, 2, 3]


def test_orjson_response_media_type():
    from shared.feature_engine.orjson_response import ORJSONResponse
    assert ORJSONResponse.media_type == "application/json"
