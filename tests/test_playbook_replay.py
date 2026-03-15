"""
Tests for ui/replay_helpers.py (Step 37 — Playbook Replay Viewer).

All tests are pure — no Streamlit, no database, no network.
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone

import pytest

# Add ui/ to path so replay_helpers can be imported directly
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_UI_DIR = os.path.join(_REPO_ROOT, "ui")
if _UI_DIR not in sys.path:
    sys.path.insert(0, _UI_DIR)

from replay_helpers import (
    REGIME_COLORS,
    SIGNAL_DETECTORS,
    available_dates_sql,
    build_detector_grid,
    extract_regime_detail,
    extract_risk_metrics,
    extract_sector_rotation,
    extract_signal_summary,
    format_snapshot_label,
    format_full_datetime,
    get_regime_color,
    get_regime_emoji,
    parse_payload,
    regime_snapshots_for_date_sql,
    risk_in_window_sql,
    signals_in_window_sql,
)


# ---------------------------------------------------------------------------
# parse_payload tests
# ---------------------------------------------------------------------------


class TestParsePayload:
    def test_dict_passthrough(self):
        d = {"regime": "GREEN", "spy_price": 500.0}
        assert parse_payload(d) == d

    def test_json_string_parsed(self):
        raw = json.dumps({"regime": "RED", "spy_price": 450.0})
        result = parse_payload(raw)
        assert result["regime"] == "RED"
        assert result["spy_price"] == 450.0

    def test_json_bytes_parsed(self):
        raw = json.dumps({"regime": "YELLOW"}).encode()
        result = parse_payload(raw)
        assert result["regime"] == "YELLOW"

    def test_invalid_json_returns_empty(self):
        assert parse_payload("not json {{{") == {}

    def test_none_returns_empty(self):
        assert parse_payload(None) == {}

    def test_int_returns_empty(self):
        assert parse_payload(42) == {}

    def test_empty_dict_returns_empty(self):
        assert parse_payload({}) == {}


# ---------------------------------------------------------------------------
# Regime color / emoji tests
# ---------------------------------------------------------------------------


class TestRegimeColors:
    def test_green_color(self):
        assert get_regime_color("GREEN") == REGIME_COLORS["GREEN"]

    def test_yellow_color(self):
        assert get_regime_color("YELLOW") == REGIME_COLORS["YELLOW"]

    def test_red_color(self):
        assert get_regime_color("RED") == REGIME_COLORS["RED"]

    def test_unknown_string_returns_unknown_color(self):
        assert get_regime_color("SOMETHING_ELSE") == REGIME_COLORS["UNKNOWN"]

    def test_none_returns_unknown_color(self):
        assert get_regime_color(None) == REGIME_COLORS["UNKNOWN"]

    def test_case_insensitive(self):
        assert get_regime_color("green") == REGIME_COLORS["GREEN"]

    def test_emoji_green(self):
        assert "🟢" in get_regime_emoji("GREEN")

    def test_emoji_red(self):
        assert "🔴" in get_regime_emoji("RED")


# ---------------------------------------------------------------------------
# extract_regime_detail tests
# ---------------------------------------------------------------------------


class TestExtractRegimeDetail:
    def test_full_payload(self):
        payload = {
            "regime": "GREEN",
            "spy_price": 510.5,
            "ema21": 505.0,
            "sma50": 498.0,
            "confidence": 0.85,
            "reason": "SPY above EMA21",
            "jnk_tlt_flag": False,
        }
        result = extract_regime_detail(payload)
        assert result["regime"] == "GREEN"
        assert result["spy_price"] == pytest.approx(510.5)
        assert result["confidence"] == pytest.approx(0.85)
        assert result["jnk_tlt_flag"] is False

    def test_missing_keys_use_defaults(self):
        result = extract_regime_detail({})
        assert result["regime"] == "UNKNOWN"
        assert result["spy_price"] == 0.0
        assert result["confidence"] == 0.0
        assert result["jnk_tlt_flag"] is False

    def test_jnk_tlt_flag_true(self):
        result = extract_regime_detail({"jnk_tlt_flag": True})
        assert result["jnk_tlt_flag"] is True


# ---------------------------------------------------------------------------
# Signal summary extraction tests
# ---------------------------------------------------------------------------


class TestExtractSignalSummary:
    def test_signal_payload_extracted(self):
        payload = {
            "pattern_name": "EpisodicPivot",
            "symbol": "AAPL",
            "confidence": 0.82,
            "entry_price": 175.5,
            "stop_price": 172.0,
        }
        result = extract_signal_summary(payload)
        assert len(result) == 1
        assert result[0]["pattern_name"] == "EpisodicPivot"
        assert result[0]["symbol"] == "AAPL"

    def test_empty_payload_returns_empty_list(self):
        assert extract_signal_summary({}) == []

    def test_list_signals_returned(self):
        payload = {"signals": [{"pattern_name": "VCP"}, {"pattern_name": "MomentumBurst"}]}
        result = extract_signal_summary(payload)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# build_detector_grid tests
# ---------------------------------------------------------------------------


class TestBuildDetectorGrid:
    def test_fired_detector_appears_in_grid(self):
        rows = [{"pattern_name": "EpisodicPivot", "symbol": "NVDA", "confidence": 0.8,
                 "entry_price": 800.0, "stop_price": 780.0}]
        grid = build_detector_grid(rows)
        assert "NVDA" in grid["EpisodicPivot"]

    def test_all_detectors_present_in_grid(self):
        grid = build_detector_grid([])
        for det in SIGNAL_DETECTORS:
            assert det in grid

    def test_unfired_detectors_have_empty_list(self):
        grid = build_detector_grid([])
        assert all(v == [] for v in grid.values())

    def test_multiple_symbols_for_same_detector(self):
        rows = [
            {"pattern_name": "VCP", "symbol": "AAPL", "confidence": 0.7,
             "entry_price": 170.0, "stop_price": 165.0},
            {"pattern_name": "VCP", "symbol": "MSFT", "confidence": 0.75,
             "entry_price": 380.0, "stop_price": 370.0},
        ]
        grid = build_detector_grid(rows)
        assert "AAPL" in grid["VCP"]
        assert "MSFT" in grid["VCP"]


# ---------------------------------------------------------------------------
# extract_risk_metrics tests
# ---------------------------------------------------------------------------


class TestExtractRiskMetrics:
    def test_full_risk_payload(self):
        payload = {"cvar_99": -0.0234, "kelly_size": 0.125, "nav": 10500.0,
                   "drawdown_snapshot": {"portfolio": 0.02}}
        result = extract_risk_metrics(payload)
        assert result["cvar_99"] == pytest.approx(-0.0234)
        assert result["kelly_size"] == pytest.approx(0.125)
        assert result["nav"] == pytest.approx(10500.0)

    def test_missing_keys_default_to_zero(self):
        result = extract_risk_metrics({})
        assert result["cvar_99"] == 0.0
        assert result["kelly_size"] == 0.0
        assert result["drawdown_snapshot"] == {}


# ---------------------------------------------------------------------------
# extract_sector_rotation tests
# ---------------------------------------------------------------------------


class TestExtractSectorRotation:
    def test_valid_sector_rotation_payload(self):
        payload = {
            "rotation_bias": "RISK_ON",
            "offensive_score": 3,
            "defensive_score": 1,
            "top_3": ["XLK", "XLY", "XLF"],
            "bottom_3": ["XLU", "XLRE", "XLP"],
        }
        result = extract_sector_rotation(payload)
        assert result is not None
        assert result["rotation_bias"] == "RISK_ON"
        assert result["top_3"] == ["XLK", "XLY", "XLF"]

    def test_none_returns_none(self):
        assert extract_sector_rotation(None) is None

    def test_empty_dict_returns_none(self):
        assert extract_sector_rotation({}) is None

    def test_missing_rotation_bias_returns_none(self):
        assert extract_sector_rotation({"top_3": ["XLK"]}) is None

    def test_json_string_payload_parsed(self):
        payload = json.dumps({
            "rotation_bias": "RISK_OFF",
            "offensive_score": 1,
            "defensive_score": 3,
            "top_3": ["XLP", "XLU", "XLV"],
            "bottom_3": ["XLK", "XLY", "XLC"],
        })
        result = extract_sector_rotation(payload)
        assert result is not None
        assert result["rotation_bias"] == "RISK_OFF"


# ---------------------------------------------------------------------------
# format_snapshot_label tests
# ---------------------------------------------------------------------------


class TestFormatSnapshotLabel:
    def test_datetime_formatted_correctly(self):
        ts = datetime(2026, 3, 15, 14, 35, 0, tzinfo=timezone.utc)
        label = format_snapshot_label(ts, "GREEN")
        assert "14:35:00" in label
        assert "GREEN" in label

    def test_no_regime_still_has_time(self):
        ts = datetime(2026, 3, 15, 9, 30, 0)
        label = format_snapshot_label(ts)
        assert "09:30" in label

    def test_format_full_datetime(self):
        ts = datetime(2026, 3, 15, 14, 35, 0, tzinfo=timezone.utc)
        result = format_full_datetime(ts)
        assert "2026-03-15" in result
        assert "14:35" in result


# ---------------------------------------------------------------------------
# SQL helpers tests
# ---------------------------------------------------------------------------


class TestSqlHelpers:
    def test_available_dates_sql_contains_playbook_logs(self):
        sql = available_dates_sql()
        assert "playbook_logs" in sql
        assert "LIMIT" in sql

    def test_regime_snapshots_sql_filters_by_log_type(self):
        sql = regime_snapshots_for_date_sql()
        assert "log_type = 'regime'" in sql
        assert "%s" in sql

    def test_signals_in_window_sql_has_interval(self):
        sql = signals_in_window_sql()
        assert "interval" in sql
        assert "signal" in sql

    def test_risk_in_window_sql_has_limit(self):
        sql = risk_in_window_sql()
        assert "LIMIT 1" in sql
        assert "risk" in sql
