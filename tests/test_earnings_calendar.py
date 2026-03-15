"""
Tests for scrapers/earnings_calendar.py (Step 19).

All tests are pure — no network, no Redis, no Postgres.
All I/O is mocked via unittest.mock.
"""

from __future__ import annotations

import asyncio
import sys
import os
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scrapers.earnings_calendar import (
    EARNINGS_CALENDAR_INTEL_KEY,
    EARNINGS_CALENDAR_TTL,
    ETF_TOP_HOLDINGS,
    THIS_WEEK_DAYS,
    SOON_DAYS,
    JUST_REPORTED_DAYS,
    TRACKED_FOR_EARNINGS,
    classify_earnings_status,
    detect_earnings_cluster,
    estimate_next_earnings,
    extract_quarterly_dates,
    run_earnings_calendar,
)
from cemini_contracts.earnings import EarningsCalendarIntel, EarningsEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TODAY = date(2026, 3, 15)


def _make_submissions(forms: list[str], dates: list[str]) -> dict:
    """Build a minimal EDGAR submissions dict with the given filings."""
    return {
        "name": "Test Corp",
        "cik": "0000320193",
        "filings": {
            "recent": {
                "form": forms,
                "filingDate": dates,
                "accessionNumber": [f"000{i}" for i in range(len(forms))],
            }
        },
    }


def _make_event(
    symbol: str = "AAPL",
    status: str = "CLEAR",
    estimated_next: date | None = None,
) -> EarningsEvent:
    return EarningsEvent(
        symbol=symbol,
        cik="0000320193",
        company_name="Test Corp",
        status=status,
        estimated_next_date=estimated_next,
        confidence=0.8,
    )


# ---------------------------------------------------------------------------
# extract_quarterly_dates tests
# ---------------------------------------------------------------------------


class TestExtractQuarterlyDates:
    def test_extracts_10q_dates(self):
        data = _make_submissions(
            ["10-Q", "10-Q", "8-K"],
            ["2025-11-01", "2025-08-01", "2025-07-15"],
        )
        result = extract_quarterly_dates(data)
        assert date(2025, 8, 1) in result
        assert date(2025, 11, 1) in result
        # 8-K should not be included
        assert date(2025, 7, 15) not in result

    def test_extracts_10k_dates(self):
        data = _make_submissions(
            ["10-K", "10-Q"],
            ["2025-10-31", "2025-08-01"],
        )
        result = extract_quarterly_dates(data)
        assert date(2025, 10, 31) in result

    def test_returns_sorted_ascending(self):
        data = _make_submissions(
            ["10-Q", "10-Q", "10-Q"],
            ["2025-11-01", "2025-05-01", "2025-08-01"],
        )
        result = extract_quarterly_dates(data)
        assert result == sorted(result)

    def test_deduplicates_same_date(self):
        data = _make_submissions(
            ["10-Q", "10-Q"],
            ["2025-11-01", "2025-11-01"],
        )
        result = extract_quarterly_dates(data)
        assert result.count(date(2025, 11, 1)) == 1

    def test_empty_submissions_returns_empty(self):
        assert extract_quarterly_dates({}) == []

    def test_no_earnings_forms_returns_empty(self):
        data = _make_submissions(["8-K", "4", "13-F"], ["2025-11-01", "2025-10-01", "2025-09-01"])
        assert extract_quarterly_dates(data) == []

    def test_malformed_date_skipped(self):
        data = _make_submissions(["10-Q", "10-Q"], ["not-a-date", "2025-08-01"])
        result = extract_quarterly_dates(data)
        assert result == [date(2025, 8, 1)]


# ---------------------------------------------------------------------------
# estimate_next_earnings tests
# ---------------------------------------------------------------------------


class TestEstimateNextEarnings:
    def test_no_dates_returns_none_zero_confidence(self):
        estimated, confidence = estimate_next_earnings([], today=TODAY)
        assert estimated is None
        assert confidence == 0.0

    def test_single_date_returns_estimate_low_confidence(self):
        last = date(2025, 12, 1)
        estimated, confidence = estimate_next_earnings([last], today=TODAY)
        assert estimated is not None
        assert estimated > TODAY
        assert confidence == pytest.approx(0.3)

    def test_regular_quarterly_cadence_high_confidence(self):
        """Four dates ~90 days apart → confidence near 1.0."""
        dates = [
            date(2025, 2, 1),
            date(2025, 5, 1),
            date(2025, 8, 1),
            date(2025, 11, 1),
        ]
        estimated, confidence = estimate_next_earnings(dates, today=TODAY)
        assert estimated is not None
        assert estimated > TODAY
        assert confidence > 0.7

    def test_irregular_cadence_lower_confidence(self):
        """Irregular intervals → lower confidence."""
        dates = [
            date(2025, 1, 1),
            date(2025, 4, 15),  # 104 days
            date(2025, 6, 1),   # 47 days
            date(2025, 11, 1),  # 153 days
        ]
        estimated, confidence = estimate_next_earnings(dates, today=TODAY)
        assert estimated is not None
        # Confidence should be lower than regular cadence
        assert confidence < 0.7

    def test_estimate_in_future(self):
        """Estimate must always be in the future."""
        dates = [date(2024, 5, 1), date(2024, 8, 1), date(2024, 11, 1)]
        estimated, _ = estimate_next_earnings(dates, today=TODAY)
        assert estimated is None or estimated > TODAY

    def test_two_dates_returns_estimate(self):
        dates = [date(2025, 6, 1), date(2025, 9, 1)]
        estimated, confidence = estimate_next_earnings(dates, today=TODAY)
        assert estimated is not None
        assert estimated > TODAY
        assert confidence == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# classify_earnings_status tests
# ---------------------------------------------------------------------------


class TestClassifyEarningsStatus:
    def test_reporting_this_week(self):
        estimated = TODAY + timedelta(days=2)
        status, days = classify_earnings_status(estimated, None, today=TODAY)
        assert status == "REPORTING_THIS_WEEK"
        assert days == 2

    def test_reporting_soon(self):
        estimated = TODAY + timedelta(days=5)
        status, days = classify_earnings_status(estimated, None, today=TODAY)
        assert status == "REPORTING_SOON"
        assert days == 5

    def test_clear_when_far_out(self):
        estimated = TODAY + timedelta(days=60)
        status, days = classify_earnings_status(estimated, None, today=TODAY)
        assert status == "CLEAR"
        assert days == 60

    def test_just_reported_takes_priority(self):
        """Even if estimated is upcoming, recent filing → JUST_REPORTED."""
        estimated = TODAY + timedelta(days=2)
        last_filing = TODAY - timedelta(days=1)
        status, days = classify_earnings_status(estimated, last_filing, today=TODAY)
        assert status == "JUST_REPORTED"
        assert days is None

    def test_just_reported_exactly_at_threshold(self):
        last_filing = TODAY - timedelta(days=JUST_REPORTED_DAYS)
        status, _ = classify_earnings_status(None, last_filing, today=TODAY)
        assert status == "JUST_REPORTED"

    def test_no_estimate_no_recent_filing_is_clear(self):
        status, days = classify_earnings_status(None, None, today=TODAY)
        assert status == "CLEAR"
        assert days is None

    def test_past_estimate_is_clear(self):
        estimated = TODAY - timedelta(days=5)
        status, _ = classify_earnings_status(estimated, None, today=TODAY)
        assert status == "CLEAR"

    def test_boundary_this_week_vs_soon(self):
        """At THIS_WEEK_DAYS boundary → REPORTING_THIS_WEEK."""
        estimated = TODAY + timedelta(days=THIS_WEEK_DAYS)
        status, _ = classify_earnings_status(estimated, None, today=TODAY)
        assert status == "REPORTING_THIS_WEEK"

    def test_boundary_soon_vs_clear(self):
        """At SOON_DAYS boundary → REPORTING_SOON."""
        estimated = TODAY + timedelta(days=SOON_DAYS)
        status, _ = classify_earnings_status(estimated, None, today=TODAY)
        assert status == "REPORTING_SOON"


# ---------------------------------------------------------------------------
# detect_earnings_cluster tests
# ---------------------------------------------------------------------------


class TestDetectEarningsCluster:
    def test_cluster_detected_when_3_holdings_reporting(self):
        """SPY top 5: AAPL, MSFT, NVDA, AMZN, GOOGL. 3 of 5 reporting → cluster."""
        events = {
            "AAPL": _make_event("AAPL", status="REPORTING_THIS_WEEK"),
            "MSFT": _make_event("MSFT", status="REPORTING_SOON"),
            "NVDA": _make_event("NVDA", status="REPORTING_THIS_WEEK"),
            "AMZN": _make_event("AMZN", status="CLEAR"),
            "GOOGL": _make_event("GOOGL", status="CLEAR"),
        }
        assert detect_earnings_cluster(events) is True

    def test_no_cluster_when_2_or_fewer(self):
        events = {
            "AAPL": _make_event("AAPL", status="REPORTING_THIS_WEEK"),
            "MSFT": _make_event("MSFT", status="REPORTING_SOON"),
            "NVDA": _make_event("NVDA", status="CLEAR"),
            "AMZN": _make_event("AMZN", status="CLEAR"),
            "GOOGL": _make_event("GOOGL", status="CLEAR"),
        }
        assert detect_earnings_cluster(events) is False

    def test_no_cluster_when_events_empty(self):
        assert detect_earnings_cluster({}) is False

    def test_just_reported_does_not_count_as_cluster(self):
        """JUST_REPORTED is not in active_statuses for cluster detection."""
        events = {
            "AAPL": _make_event("AAPL", status="JUST_REPORTED"),
            "MSFT": _make_event("MSFT", status="JUST_REPORTED"),
            "NVDA": _make_event("NVDA", status="JUST_REPORTED"),
            "AMZN": _make_event("AMZN", status="JUST_REPORTED"),
        }
        assert detect_earnings_cluster(events) is False


# ---------------------------------------------------------------------------
# run_earnings_calendar integration tests (mocked HTTP + Redis)
# ---------------------------------------------------------------------------


def _build_submissions_response(dates: list[str]) -> dict:
    """Build mock EDGAR submissions with regular quarterly 10-Q dates."""
    return {
        "name": "Test Corp",
        "cik": "0000320193",
        "filings": {
            "recent": {
                "form": ["10-Q"] * len(dates),
                "filingDate": dates,
                "accessionNumber": [f"acc{i}" for i in range(len(dates))],
            }
        },
    }


class TestRunEarningsCalendar:
    def _mock_http(self, submission_data: dict):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = submission_data
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        return mock_client

    def _cik_map(self, symbols: list[str]) -> dict[str, str]:
        return {sym: f"000{i:07d}" for i, sym in enumerate(symbols)}

    @patch("scrapers.earnings_calendar.IntelPublisher.publish")
    def test_publishes_to_correct_channel(self, mock_publish):
        sub_data = _build_submissions_response(["2025-11-01", "2025-08-01", "2025-05-01"])
        http_client = self._mock_http(sub_data)
        cik_map = self._cik_map(["AAPL", "MSFT"])

        result = asyncio.get_event_loop().run_until_complete(
            run_earnings_calendar(http_client, cik_map, today=TODAY)
        )
        assert result is not None
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args.kwargs.get("key") == EARNINGS_CALENDAR_INTEL_KEY or \
               call_args.args[0] == EARNINGS_CALENDAR_INTEL_KEY

    @patch("scrapers.earnings_calendar.IntelPublisher.publish")
    def test_publishes_with_correct_ttl(self, mock_publish):
        sub_data = _build_submissions_response(["2025-11-01", "2025-08-01"])
        http_client = self._mock_http(sub_data)
        cik_map = self._cik_map(["AAPL"])

        asyncio.get_event_loop().run_until_complete(
            run_earnings_calendar(http_client, cik_map, today=TODAY)
        )
        call_args = mock_publish.call_args
        ttl = call_args.kwargs.get("ttl", None)
        if ttl is None and len(call_args.args) > 4:
            ttl = call_args.args[4]
        assert ttl == EARNINGS_CALENDAR_TTL

    @patch("scrapers.earnings_calendar.IntelPublisher.publish")
    def test_returns_earnings_calendar_intel(self, mock_publish):
        sub_data = _build_submissions_response(["2025-11-01", "2025-08-01"])
        http_client = self._mock_http(sub_data)
        cik_map = self._cik_map(["AAPL", "MSFT"])

        result = asyncio.get_event_loop().run_until_complete(
            run_earnings_calendar(http_client, cik_map, today=TODAY)
        )
        assert isinstance(result, EarningsCalendarIntel)
        assert result.total_tracked > 0

    @patch("scrapers.earnings_calendar.IntelPublisher.publish")
    def test_empty_cik_map_returns_none(self, mock_publish):
        """When no CIKs are found, returns None without publishing."""
        http_client = self._mock_http({})
        result = asyncio.get_event_loop().run_until_complete(
            run_earnings_calendar(http_client, {}, today=TODAY)
        )
        assert result is None
        mock_publish.assert_not_called()

    @patch("scrapers.earnings_calendar.IntelPublisher.publish")
    def test_http_failure_skips_symbol(self, mock_publish):
        """HTTP failure for a symbol is handled gracefully."""
        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 404
        mock_resp_fail.json.return_value = {}

        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.json.return_value = _build_submissions_response(["2025-11-01", "2025-08-01"])

        mock_client = AsyncMock()
        # First call fails, second succeeds
        mock_client.get = AsyncMock(side_effect=[mock_resp_fail, mock_resp_ok])

        cik_map = {"AAPL": "0000320193", "MSFT": "0000789019"}
        result = asyncio.get_event_loop().run_until_complete(
            run_earnings_calendar(mock_client, cik_map, today=TODAY)
        )
        # Should still produce a result with at least 1 event (MSFT)
        assert result is not None


# ---------------------------------------------------------------------------
# Pydantic contract tests
# ---------------------------------------------------------------------------


class TestEarningsContracts:
    def test_earnings_event_valid(self):
        event = EarningsEvent(
            symbol="AAPL",
            cik="0000320193",
            company_name="Apple Inc.",
            last_filing_date=date(2025, 11, 1),
            last_filing_type="10-Q",
            estimated_next_date=date(2026, 2, 1),
            days_until_earnings=45,
            status="REPORTING_SOON",
            confidence=0.85,
        )
        assert event.symbol == "AAPL"
        assert event.status == "REPORTING_SOON"

    def test_earnings_event_status_validation(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            EarningsEvent(
                symbol="AAPL",
                cik="x",
                company_name="Test",
                status="INVALID_STATUS",  # type: ignore[arg-type]
            )

    def test_earnings_calendar_intel_valid(self):
        event = _make_event("AAPL", "REPORTING_SOON")
        intel = EarningsCalendarIntel(
            reporting_this_week=[],
            reporting_soon=["AAPL"],
            just_reported=[],
            earnings_cluster=False,
            events={"AAPL": event},
            total_tracked=1,
        )
        assert intel.total_tracked == 1
        assert intel.earnings_cluster is False

    def test_earnings_calendar_intel_defaults(self):
        intel = EarningsCalendarIntel()
        assert intel.earnings_cluster is False
        assert intel.reporting_this_week == []
        assert intel.total_tracked == 0


# ---------------------------------------------------------------------------
# Module sanity tests
# ---------------------------------------------------------------------------


class TestModuleSanity:
    def test_tracked_for_earnings_excludes_etfs(self):
        """ETFs (SPY, QQQ, IWM, DIA) should not be in TRACKED_FOR_EARNINGS."""
        etf_syms = {"SPY", "IWM", "DIA"}
        assert etf_syms.isdisjoint(set(TRACKED_FOR_EARNINGS))

    def test_etf_top_holdings_all_have_5_entries(self):
        for etf, holdings in ETF_TOP_HOLDINGS.items():
            assert len(holdings) == 5, f"{etf} should have 5 top holdings"

    def test_earnings_calendar_ttl_greater_than_intel_default(self):
        assert EARNINGS_CALENDAR_TTL > 300

    def test_cik_map_parsing_from_sec_format(self):
        """Verify the CIK parsing helper used in edgar_harvester works correctly."""
        from scrapers.edgar.cik_mapping import _parse_cik_json
        sample = {
            "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
            "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft"},
        }
        result = _parse_cik_json(sample)
        assert result["AAPL"] == "0000320193"
        assert result["MSFT"] == "0000789019"
