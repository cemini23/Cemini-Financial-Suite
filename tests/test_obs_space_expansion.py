"""tests/test_obs_space_expansion.py — Step 50b: RL Observation Space Expansion tests.

Tests for 10 new features wired from vol_surface_log, sector_rotation_log,
and earnings_calendar.  All DB calls are mocked; tests are pure.
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest


# ── helpers ────────────────────────────────────────────────────────────────────

def make_ticks(n: int = 200, seed: int = 42) -> pl.DataFrame:
    """Synthetic 1-min OHLCV, same style as test_feature_engine.py."""
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.standard_normal(n) * 0.5)
    timestamps = pl.datetime_range(
        pl.datetime(2026, 3, 1, 0, 0, 0),
        pl.datetime(2026, 3, 1, 0, 0, 0) + pl.duration(minutes=n - 1),
        "1m",
        eager=True,
    )
    return pl.DataFrame({
        "timestamp": timestamps,
        "open": (close + 0.05).tolist(),
        "high": (close + 0.3).tolist(),
        "low": (close - 0.3).tolist(),
        "close": close.tolist(),
        "volume": rng.integers(1000, 100_000, n).astype(float).tolist(),
    })


def _build_matrix_patched(df: pl.DataFrame, vol_df=None, rot_df=None, ep_result=(0.0, 0)):
    """Build feature matrix with all DB loaders mocked."""
    from shared.feature_engine.feature_matrix import build_feature_matrix

    vol_side = Exception("no db") if vol_df is None else None
    rot_side = Exception("no db") if rot_df is None else None

    vol_patch = (
        patch("shared.feature_engine.feature_matrix.data_loader.load_vol_surface",
              side_effect=vol_side)
        if vol_df is None else
        patch("shared.feature_engine.feature_matrix.data_loader.load_vol_surface",
              return_value=vol_df)
    )
    rot_patch = (
        patch("shared.feature_engine.feature_matrix.data_loader.load_sector_rotation",
              side_effect=rot_side)
        if rot_df is None else
        patch("shared.feature_engine.feature_matrix.data_loader.load_sector_rotation",
              return_value=rot_df)
    )

    with (
        patch("shared.feature_engine.feature_matrix.data_loader.load_market_ticks",
              return_value=df),
        patch("shared.feature_engine.feature_matrix.data_loader.load_macro_logs",
              side_effect=Exception("no db")),
        patch("shared.feature_engine.feature_matrix.data_loader.load_playbook_regime",
              side_effect=Exception("no db")),
        vol_patch,
        rot_patch,
        patch("shared.feature_engine.feature_matrix.data_loader.load_earnings_proximity",
              return_value=ep_result),
    ):
        return build_feature_matrix("AAPL", "2026-01-01", "2026-04-01")


# ── FEATURE REGISTRY tests ─────────────────────────────────────────────────────

def test_feature_registry_has_28_features():
    from shared.feature_engine.config import FEATURE_REGISTRY
    assert len(FEATURE_REGISTRY) == 28


def test_feature_registry_indices_contiguous():
    from shared.feature_engine.config import FEATURE_REGISTRY
    indices = sorted(v["index"] for v in FEATURE_REGISTRY.values())
    assert indices == list(range(28))


def test_feature_registry_expansion_features_present():
    from shared.feature_engine.config import FEATURE_REGISTRY
    for key in ["realized_vol_21d", "vol_regime_low", "vol_regime_normal", "vol_regime_high",
                "beta_to_spy", "rot_risk_on", "rot_risk_off", "rot_neutral",
                "earnings_proximity", "earnings_cluster"]:
        assert key in FEATURE_REGISTRY, f"Missing from FEATURE_REGISTRY: {key}"


def test_feature_registry_beta_has_clip_norm():
    from shared.feature_engine.config import FEATURE_REGISTRY
    assert FEATURE_REGISTRY["beta_to_spy"]["norm"] == "clip"
    assert FEATURE_REGISTRY["beta_to_spy"]["range"] == [-3, 3]


def test_feature_registry_earnings_cluster_is_binary():
    from shared.feature_engine.config import FEATURE_REGISTRY
    assert FEATURE_REGISTRY["earnings_cluster"]["norm"] == "binary"


# ── ALL_FEATURES expansion tests ───────────────────────────────────────────────

def test_all_features_expanded_to_28():
    from shared.feature_engine.config import ALL_FEATURES
    assert len(ALL_FEATURES) == 28


def test_feature_vector_dim_updated_to_28():
    from shared.feature_engine.config import FEATURE_VECTOR_DIM
    assert FEATURE_VECTOR_DIM == 28


def test_all_expansion_feature_names_present():
    from shared.feature_engine.config import ALL_FEATURES
    names = {f.name for f in ALL_FEATURES}
    for expected in [
        "realized_vol_21d", "vol_regime_low", "vol_regime_normal", "vol_regime_high",
        "beta_to_spy", "rot_risk_on", "rot_risk_off", "rot_neutral",
        "earnings_proximity", "earnings_cluster",
    ]:
        assert expected in names, f"Missing: {expected}"


# ── One-hot encoding correctness ───────────────────────────────────────────────

def test_vol_regime_onehot_sums_to_one():
    df = pl.DataFrame({"vol_regime_str": ["LOW", "NORMAL", "HIGH", "NORMAL", "LOW"]})
    df = df.with_columns([
        (pl.col("vol_regime_str") == "LOW").cast(pl.Float64).alias("vol_regime_low"),
        (pl.col("vol_regime_str") == "NORMAL").cast(pl.Float64).alias("vol_regime_normal"),
        (pl.col("vol_regime_str") == "HIGH").cast(pl.Float64).alias("vol_regime_high"),
    ])
    for i in range(len(df)):
        row_sum = df["vol_regime_low"][i] + df["vol_regime_normal"][i] + df["vol_regime_high"][i]
        assert abs(row_sum - 1.0) < 1e-9


def test_rotation_bias_onehot_sums_to_one():
    df = pl.DataFrame({"rotation_bias": ["RISK_ON", "RISK_OFF", "NEUTRAL", "RISK_ON"]})
    df = df.with_columns([
        (pl.col("rotation_bias") == "RISK_ON").cast(pl.Float64).alias("rot_risk_on"),
        (pl.col("rotation_bias") == "RISK_OFF").cast(pl.Float64).alias("rot_risk_off"),
        (pl.col("rotation_bias") == "NEUTRAL").cast(pl.Float64).alias("rot_neutral"),
    ])
    for i in range(len(df)):
        row_sum = df["rot_risk_on"][i] + df["rot_risk_off"][i] + df["rot_neutral"][i]
        assert abs(row_sum - 1.0) < 1e-9


# ── Earnings proximity math ────────────────────────────────────────────────────

def test_earnings_proximity_zero_days():
    days_until = 0
    proximity = 1.0 / (days_until + 1)
    assert abs(proximity - 1.0) < 1e-9


def test_earnings_proximity_seven_days():
    days_until = 7
    proximity = 1.0 / (days_until + 1)
    assert abs(proximity - 0.125) < 1e-9


def test_earnings_proximity_clear_returns_zero():
    """load_earnings_proximity returns (0.0, 0) when no non-CLEAR rows found."""
    with patch("shared.feature_engine.data_loader._psycopg2_fetch", return_value=([], [])):
        from shared.feature_engine.data_loader import load_earnings_proximity
        ep, ec = load_earnings_proximity("AAPL", "2026-03-15")
    assert ep == 0.0
    assert ec == 0


# ── beta_to_spy clipping ───────────────────────────────────────────────────────

def test_beta_to_spy_clips_above_3():
    series = pl.Series("beta_to_spy", [5.0, 3.5, 3.0])
    clipped = series.clip(-3.0, 3.0)
    assert clipped[0] == 3.0
    assert clipped[1] == 3.0
    assert clipped[2] == 3.0


def test_beta_to_spy_clips_below_minus_3():
    series = pl.Series("beta_to_spy", [-5.0, -4.0, -3.0])
    clipped = series.clip(-3.0, 3.0)
    assert clipped[0] == -3.0
    assert clipped[1] == -3.0
    assert clipped[2] == -3.0


def test_beta_to_spy_midrange_unchanged():
    series = pl.Series("beta_to_spy", [0.5, -1.2, 2.9])
    clipped = series.clip(-3.0, 3.0)
    assert abs(clipped[0] - 0.5) < 1e-9
    assert abs(clipped[1] + 1.2) < 1e-9
    assert abs(clipped[2] - 2.9) < 1e-9


# ── join_asof backward alignment ──────────────────────────────────────────────

def test_join_asof_backward_snapshot_alignment():
    """30-min snapshot at 09:00 should fill all ticks until the 09:30 snapshot."""
    ticks = pl.DataFrame({
        "timestamp": [
            datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 9, 15),
            datetime(2026, 3, 1, 9, 30), datetime(2026, 3, 1, 9, 45),
        ],
        "value": [1.0, 2.0, 3.0, 4.0],
    })
    snapshots = pl.DataFrame({
        "timestamp": [datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 9, 30)],
        "rotation_bias": ["RISK_ON", "NEUTRAL"],
    })
    result = ticks.join_asof(snapshots.sort("timestamp"), on="timestamp", strategy="backward")
    assert result["rotation_bias"][0] == "RISK_ON"
    assert result["rotation_bias"][1] == "RISK_ON"   # 09:15 uses 09:00 snapshot
    assert result["rotation_bias"][2] == "NEUTRAL"   # 09:30 uses 09:30 snapshot
    assert result["rotation_bias"][3] == "NEUTRAL"   # 09:45 uses 09:30 snapshot


def test_join_asof_no_future_data_gives_null():
    """Ticks before the first snapshot should get null (backward strategy)."""
    ticks = pl.DataFrame({
        "timestamp": [datetime(2026, 3, 1, 8, 0), datetime(2026, 3, 1, 9, 30)],
    })
    snapshots = pl.DataFrame({
        "timestamp": [datetime(2026, 3, 1, 9, 30)],
        "bias": ["RISK_ON"],
    })
    result = ticks.join_asof(snapshots.sort("timestamp"), on="timestamp", strategy="backward")
    assert result["bias"][0] is None    # before snapshot → null
    assert result["bias"][1] == "RISK_ON"


# ── Full feature matrix with all defaults ──────────────────────────────────────

def test_feature_matrix_has_28_columns():
    df = make_ticks(200)
    result = _build_matrix_patched(df)
    from shared.feature_engine.config import ALL_FEATURES
    feature_cols = [f.name for f in ALL_FEATURES]
    present = [c for c in feature_cols if c in result.columns]
    assert len(present) == 28


def test_feature_matrix_no_nan_with_defaults():
    """All expansion defaults are non-NaN."""
    df = make_ticks(200, seed=1)
    result = _build_matrix_patched(df)
    from shared.feature_engine.config import ALL_FEATURES
    feature_cols = [f.name for f in ALL_FEATURES if f.name in result.columns]
    null_count = result.select(feature_cols).null_count().sum_horizontal()[0]
    assert null_count == 0, f"Unexpected nulls: {null_count}"


def test_vol_regime_defaults_to_normal():
    df = make_ticks(200, seed=2)
    result = _build_matrix_patched(df)
    assert result["vol_regime_normal"].mean() == 1.0
    assert result["vol_regime_low"].mean() == 0.0
    assert result["vol_regime_high"].mean() == 0.0


def test_rotation_defaults_to_neutral():
    df = make_ticks(200, seed=3)
    result = _build_matrix_patched(df)
    assert result["rot_neutral"].mean() == 1.0
    assert result["rot_risk_on"].mean() == 0.0
    assert result["rot_risk_off"].mean() == 0.0


def test_beta_default_is_1():
    df = make_ticks(200, seed=4)
    result = _build_matrix_patched(df)
    assert result["beta_to_spy"].mean() == 1.0


# ── Feature matrix with real data ─────────────────────────────────────────────

def test_vol_surface_high_regime_overrides_default():
    """Mocked vol_surface with HIGH regime must override NORMAL default."""
    df = make_ticks(200, seed=5)
    vol_df = pl.DataFrame({
        "timestamp": [datetime(2026, 3, 1, 0, 0)],
        "realized_vol_21d": [0.35],
        "vol_regime_str": ["HIGH"],
        "beta_to_spy": [1.8],
    })
    result = _build_matrix_patched(df, vol_df=vol_df)
    assert result["vol_regime_high"].mean() == 1.0
    assert result["vol_regime_normal"].mean() == 0.0
    assert result["vol_regime_low"].mean() == 0.0


def test_sector_rotation_risk_on_overrides_neutral():
    """Mocked sector_rotation with RISK_ON must override NEUTRAL default."""
    df = make_ticks(200, seed=6)
    rot_df = pl.DataFrame({
        "timestamp": [datetime(2026, 3, 1, 0, 0)],
        "rotation_bias": ["RISK_ON"],
    })
    result = _build_matrix_patched(df, rot_df=rot_df)
    assert result["rot_risk_on"].mean() == 1.0
    assert result["rot_neutral"].mean() == 0.0


def test_earnings_proximity_applied_from_loader():
    """Mocked (0.5, 1) proximity/cluster must appear in all rows."""
    df = make_ticks(200, seed=7)
    result = _build_matrix_patched(df, ep_result=(0.5, 1))
    assert result["earnings_proximity"].mean() == pytest.approx(0.5, abs=1e-6)
    assert result["earnings_cluster"].mean() == 1.0


# ── Data loader unit tests ────────────────────────────────────────────────────

def test_load_vol_surface_empty_on_no_rows():
    with patch("shared.feature_engine.data_loader._psycopg2_fetch", return_value=([], [])):
        from shared.feature_engine.data_loader import load_vol_surface
        result = load_vol_surface("AAPL", "2026-01-01", "2026-02-01")
    assert result.is_empty()
    assert "timestamp" in result.schema
    assert "realized_vol_21d" in result.schema


def test_load_sector_rotation_empty_on_no_rows():
    with patch("shared.feature_engine.data_loader._psycopg2_fetch", return_value=([], [])):
        from shared.feature_engine.data_loader import load_sector_rotation
        result = load_sector_rotation("2026-01-01", "2026-02-01")
    assert result.is_empty()
    assert "timestamp" in result.schema
    assert "rotation_bias" in result.schema
