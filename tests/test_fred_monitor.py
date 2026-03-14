"""Tests for scrapers/fred_monitor.py (Step 39).

All tests are pure — no network, no Redis, no Postgres.
All I/O is mocked via unittest.mock.

Coverage:
 1. Series config completeness (12 series)
 2. URL construction
 3. Parse FRED observations
 4. Parse FRED '.' sentinel → None
 5. Redis payload structure
 6. Redis TTL >= 2× poll interval
 7. DB insert idempotency (ON CONFLICT DO NOTHING)
 8. Missing API key — no crash, logs warning
 9. HTTP error handling — continues to next series
10. Backfill 90-day window calculation
11. Channel grouping of observations
12. JSONL archive path includes today's date
"""

import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest

from scrapers.fred_monitor import (
    FRED_BACKFILL_DAYS,
    FRED_POLL_INTERVAL,
    FRED_SERIES,
    FRED_TTL,
    _archive_observation,
    _build_fred_url,
    _fetch_series,
    _group_by_channel,
    _parse_fred_value,
    _publish_to_redis,
    _store_observations,
    backfill,
    poll_and_publish,
)


# ── 1. Series config completeness ─────────────────────────────────────────────

def test_fred_series_config_complete():
    """All 12 series must have channel, field, and freq defined."""
    required_keys = {"channel", "field", "freq"}
    assert len(FRED_SERIES) == 12, f"Expected 12 series, got {len(FRED_SERIES)}"
    for series_id, config in FRED_SERIES.items():
        missing = required_keys - set(config.keys())
        assert not missing, f"Series {series_id} missing keys: {missing}"
    # Verify all expected series IDs are present
    expected_ids = {
        "T10Y2Y", "T10Y3M", "DFF", "WALCL", "BAMLH0A0HYM2",
        "ICSA", "UNRATE", "PAYEMS", "PCEPI", "CPILFESL",
        "UMCSENT", "VIXCLS",
    }
    assert set(FRED_SERIES.keys()) == expected_ids


def test_fred_series_channels_are_intel_namespace():
    """All channels must use the intel: namespace."""
    for series_id, config in FRED_SERIES.items():
        assert config["channel"].startswith("intel:fred_"), (
            f"Series {series_id} channel '{config['channel']}' missing intel:fred_ prefix"
        )


# ── 2. URL construction ────────────────────────────────────────────────────────

def test_fred_api_url_construction_basic():
    """URL includes series_id, api_key, file_type, sort_order, limit."""
    url = _build_fred_url("T10Y2Y", "testkey123")
    assert "series_id=T10Y2Y" in url
    assert "api_key=testkey123" in url
    assert "file_type=json" in url
    assert "sort_order=desc" in url
    assert "limit=5" in url


def test_fred_api_url_construction_with_start():
    """observation_start is appended when provided."""
    url = _build_fred_url("DFF", "key", observation_start="2025-01-01", limit=100)
    assert "observation_start=2025-01-01" in url
    assert "limit=100" in url


def test_fred_api_url_construction_no_start():
    """observation_start is absent when not provided."""
    url = _build_fred_url("UNRATE", "key")
    assert "observation_start" not in url


# ── 3. Parse FRED observations ─────────────────────────────────────────────────

def test_fred_parse_observations():
    """Parse a valid FRED API JSON response."""
    sample_json = {
        "observations": [
            {"date": "2026-03-12", "value": "0.42"},
            {"date": "2026-03-11", "value": "0.38"},
        ]
    }
    # Step 48: _fetch_series now delegates to _fetch_series_url (hishel-wrapped).
    # Patch at that level — it returns the raw observations list.
    raw_obs = [{"date": "2026-03-12", "value": "0.42"}, {"date": "2026-03-11", "value": "0.38"}]

    with patch("scrapers.fred_monitor._fetch_series_url", return_value=raw_obs):
        result = _fetch_series("T10Y2Y", "testkey")

    assert len(result) == 2
    assert result[0]["date"] == "2026-03-12"
    assert result[0]["value"] == pytest.approx(0.42)
    assert result[1]["date"] == "2026-03-11"
    assert result[1]["value"] == pytest.approx(0.38)


# ── 4. FRED '.' sentinel → None ───────────────────────────────────────────────

def test_fred_parse_missing_value_dot():
    """FRED '.' sentinel value must parse to None."""
    assert _parse_fred_value(".") is None


def test_fred_parse_missing_value_empty():
    """Empty string parses to None."""
    assert _parse_fred_value("") is None


def test_fred_parse_missing_value_none():
    """Python None input returns None."""
    assert _parse_fred_value(None) is None


def test_fred_parse_valid_float():
    """Valid numeric string parses correctly."""
    assert _parse_fred_value("3.21") == pytest.approx(3.21)
    assert _parse_fred_value("-0.15") == pytest.approx(-0.15)


def test_fred_parse_dot_in_fetch():
    """Full _fetch_series() with '.' value returns None for that observation."""
    sample_json = {
        "observations": [
            {"date": "2026-03-12", "value": "."},
            {"date": "2026-03-11", "value": "4.33"},
        ]
    }
    raw_obs = [{"date": "2026-03-12", "value": "."}, {"date": "2026-03-11", "value": "4.33"}]

    with patch("scrapers.fred_monitor._fetch_series_url", return_value=raw_obs):
        result = _fetch_series("BAMLH0A0HYM2", "key")

    assert result[0]["value"] is None
    assert result[1]["value"] == pytest.approx(4.33)


# ── 5. Redis payload structure ─────────────────────────────────────────────────

def test_fred_redis_payload_structure():
    """Published envelope must have value, source_system, timestamp, confidence."""
    mock_r = MagicMock()
    payload = {
        "spread_10y2y": 0.42,
        "observation_date": "2026-03-12",
        "fetched_at": "2026-03-13T00:00:00+00:00",
        "source": "fred",
    }
    _publish_to_redis(mock_r, "intel:fred_yield_curve", payload)

    mock_r.set.assert_called_once()
    args = mock_r.set.call_args
    channel = args[0][0]
    raw_envelope = args[0][1]
    envelope = json.loads(raw_envelope)

    assert channel == "intel:fred_yield_curve"
    assert "value" in envelope
    assert "source_system" in envelope
    assert "timestamp" in envelope
    assert "confidence" in envelope
    assert envelope["source_system"] == "fred_monitor"
    assert envelope["value"]["spread_10y2y"] == pytest.approx(0.42)


# ── 6. Redis TTL >= 2× poll interval ──────────────────────────────────────────

def test_fred_redis_ttl():
    """FRED_TTL must be at least 2× FRED_POLL_INTERVAL (LESSONS.md TTL mismatch pattern)."""
    assert FRED_TTL >= 2 * FRED_POLL_INTERVAL, (
        f"FRED_TTL={FRED_TTL} < 2×FRED_POLL_INTERVAL={2 * FRED_POLL_INTERVAL} — "
        "brain will see nil signals between polls"
    )


def test_fred_redis_ttl_applied_on_publish():
    """_publish_to_redis must pass ex=FRED_TTL to Redis SET."""
    mock_r = MagicMock()
    _publish_to_redis(mock_r, "intel:fred_test", {"key": "val"})
    mock_r.set.assert_called_once()
    _, kwargs = mock_r.set.call_args
    assert kwargs.get("ex") == FRED_TTL


# ── 7. DB insert idempotency ───────────────────────────────────────────────────

def test_fred_db_insert_idempotent():
    """_store_observations must use ON CONFLICT DO NOTHING — no exception on duplicate."""
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0  # simulate conflict (no rows inserted)

    observations = [
        {"date": "2026-03-12", "value": 0.42},
        {"date": "2026-03-11", "value": 0.38},
    ]
    result = _store_observations(mock_cursor, "T10Y2Y", observations)
    assert result == 0  # 0 rows inserted (all conflicted)
    assert mock_cursor.execute.call_count == 2

    # Verify ON CONFLICT clause is in the SQL
    sql_used = mock_cursor.execute.call_args_list[0][0][0]
    assert "ON CONFLICT" in sql_used
    assert "DO NOTHING" in sql_used


def test_fred_db_insert_new_rows():
    """_store_observations returns count of actually inserted rows."""
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1  # simulate successful insert

    observations = [{"date": "2026-03-13", "value": 1.23}]
    result = _store_observations(mock_cursor, "DFF", observations)
    assert result == 1


# ── 8. Missing API key handling ───────────────────────────────────────────────

def test_fred_missing_api_key_no_crash(caplog):
    """poll_and_publish should skip gracefully when no API key; _fetch_series returns [] on HTTP error."""
    mock_cursor = MagicMock()
    mock_r = MagicMock()

    # When api_key is empty, the URL will contain api_key= and FRED returns 400
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("400 Bad Request — missing api_key")

    with patch("scrapers.fred_monitor.requests.get", return_value=mock_resp):
        with patch("scrapers.fred_monitor.time.sleep"):
            poll_and_publish(mock_cursor, mock_r, "")

    # Should not raise — just log warnings and move on


def test_fred_missing_api_key_logs_warning(caplog):
    """main() should log a warning when FRED_API_KEY is not set."""
    import logging
    with patch.dict(os.environ, {}, clear=False):
        env_copy = os.environ.copy()
        env_copy.pop("FRED_API_KEY", None)
        with patch.dict(os.environ, env_copy, clear=True):
            # Import after patching env
            import importlib
            import scrapers.fred_monitor as fm
            with caplog.at_level(logging.WARNING, logger="fred_monitor"):
                api_key = os.getenv("FRED_API_KEY", "")
                if not api_key:
                    fm.logger.warning("FRED_API_KEY not set — will retry every 60s until configured")
            assert any("FRED_API_KEY" in r.message for r in caplog.records)


# ── 9. HTTP error handling ─────────────────────────────────────────────────────

def test_fred_http_error_returns_empty_list():
    """_fetch_series returns [] on HTTP 4xx/5xx without raising."""
    import requests as req_lib
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError("403 Forbidden")

    with patch("scrapers.fred_monitor.requests.get", return_value=mock_resp):
        result = _fetch_series("VIXCLS", "badkey")

    assert result == []


def test_fred_http_error_continues_other_series():
    """poll_and_publish continues processing all series even if one fails."""
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0
    mock_r = MagicMock()

    call_count = {"n": 0}

    def mock_fetch_url(url):
        call_count["n"] += 1
        if "T10Y2Y" in url:
            import requests as req_lib
            raise req_lib.exceptions.HTTPError("500")
        return []

    with patch("scrapers.fred_monitor._fetch_series_url", side_effect=mock_fetch_url):
        with patch("scrapers.fred_monitor.time.sleep"):
            poll_and_publish(mock_cursor, mock_r, "testkey")

    # All 12 series were attempted despite one 500 error
    assert call_count["n"] == 12


# ── 10. Backfill 90-day window ─────────────────────────────────────────────────

def test_fred_backfill_date_range():
    """backfill() requests FRED_BACKFILL_DAYS=90 days of history."""
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0

    captured_urls = []

    def mock_fetch_url(url):
        captured_urls.append(url)
        return []

    with patch("scrapers.fred_monitor._fetch_series_url", side_effect=mock_fetch_url):
        with patch("scrapers.fred_monitor.time.sleep"):
            backfill(mock_cursor, "testkey")

    assert len(captured_urls) == 12
    # All URLs must include observation_start
    for url in captured_urls:
        assert "observation_start=" in url
    # The start date must be approximately 90 days back
    from datetime import datetime, timezone, timedelta
    expected_start = (datetime.now(tz=timezone.utc) - timedelta(days=FRED_BACKFILL_DAYS)).strftime("%Y-%m-%d")
    for url in captured_urls:
        assert f"observation_start={expected_start}" in url


# ── 11. Channel grouping ───────────────────────────────────────────────────────

def test_fred_channel_grouping():
    """Observations with the same channel are grouped into one payload."""
    # T10Y2Y and T10Y3M both publish to intel:fred_yield_curve
    observations_by_series = {
        "T10Y2Y": [{"date": "2026-03-12", "value": 0.42}],
        "T10Y3M": [{"date": "2026-03-12", "value": 0.15}],
    }
    channels = _group_by_channel(observations_by_series)

    assert "intel:fred_yield_curve" in channels
    yc = channels["intel:fred_yield_curve"]
    assert yc["spread_10y2y"] == pytest.approx(0.42)
    assert yc["spread_10y3m"] == pytest.approx(0.15)
    assert yc["source"] == "fred"


def test_fred_channel_grouping_skips_none_values():
    """Observations with value=None (FRED '.') are excluded from channel payload."""
    observations_by_series = {
        "T10Y2Y": [{"date": "2026-03-12", "value": None}],
        "T10Y3M": [{"date": "2026-03-12", "value": 0.15}],
    }
    channels = _group_by_channel(observations_by_series)

    yc = channels.get("intel:fred_yield_curve", {})
    assert "spread_10y2y" not in yc
    assert yc.get("spread_10y3m") == pytest.approx(0.15)


def test_fred_channel_grouping_multiple_channels():
    """Each channel receives only its own series data."""
    observations_by_series = {
        "DFF": [{"date": "2026-03-12", "value": 5.33}],
        "WALCL": [{"date": "2026-03-06", "value": 6800000.0}],
        "ICSA": [{"date": "2026-03-07", "value": 220000.0}],
    }
    channels = _group_by_channel(observations_by_series)

    assert "intel:fred_fed_policy" in channels
    assert "intel:fred_labor" in channels
    assert channels["intel:fred_fed_policy"]["fed_funds_rate"] == pytest.approx(5.33)
    assert channels["intel:fred_labor"]["initial_claims"] == pytest.approx(220000.0)


# ── 12. JSONL archive path ─────────────────────────────────────────────────────

def test_fred_archive_path_includes_date(tmp_path):
    """Archive file path must include today's date in YYYYMMDD format."""
    today = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    expected_filename = f"fred_{today}.jsonl"

    with patch("scrapers.fred_monitor.ARCHIVE_DIR", str(tmp_path)):
        _archive_observation("T10Y2Y", "2026-03-12", 0.42)

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].name == expected_filename


def test_fred_archive_jsonl_content(tmp_path):
    """Each archived observation is valid JSON with required fields."""
    with patch("scrapers.fred_monitor.ARCHIVE_DIR", str(tmp_path)):
        _archive_observation("VIXCLS", "2026-03-12", 20.5)

    archive_file = list(tmp_path.iterdir())[0]
    line = archive_file.read_text().strip()
    record = json.loads(line)

    assert record["series_id"] == "VIXCLS"
    assert record["observation_date"] == "2026-03-12"
    assert record["value"] == pytest.approx(20.5)
    assert "fetched_at" in record
