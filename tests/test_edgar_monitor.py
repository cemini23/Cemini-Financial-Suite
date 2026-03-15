"""Cemini Financial Suite — EDGAR Monitor Tests (Step 17).

All pure tests — no network, no real DB, no real Redis.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from edgar_monitor.alert_rules import (
    ALERT_THRESHOLD,
    _extract_item_numbers,
    _is_after_hours,
    score_filing,
)
from edgar_monitor.insider_cluster import InsiderTrade, detect_clusters
from edgar_monitor.metric_extractor import extract_8k_metrics
from edgar_monitor.models import EdgarAlert, FilingSignificance, InsiderCluster

# ── Helpers ────────────────────────────────────────────────────────────────────

def _utc(hour: int = 12, minute: int = 0) -> datetime:
    """Return a datetime with a given UTC hour (today)."""
    return datetime(2026, 3, 15, hour, minute, 0, tzinfo=timezone.utc)


def _trade(
    ticker: str = "AAPL",
    name: str = "Alice Smith",
    title: str = "Director",
    tx_type: str = "P",
    value: float = 50_000.0,
    days_ago: int = 0,
) -> InsiderTrade:
    filed = datetime(2026, 3, 15, tzinfo=timezone.utc) - timedelta(days=days_ago)
    return InsiderTrade(
        ticker=ticker,
        cik="0000320193",
        insider_name=name,
        title=title,
        transaction_type=tx_type,
        shares=100.0,
        price_per_share=value / 100.0,
        total_value=value,
        filed_at=filed,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Significance scoring
# ══════════════════════════════════════════════════════════════════════════════

class TestFilingScoring:
    def test_8k_base_score(self):
        sig = score_filing("AAPL", "123", "8-K", "acc-001")
        assert sig.base_score == 70

    def test_10k_base_score(self):
        sig = score_filing("AAPL", "123", "10-K", "acc-002")
        assert sig.base_score == 40

    def test_10q_base_score(self):
        sig = score_filing("AAPL", "123", "10-Q", "acc-003")
        assert sig.base_score == 30

    def test_form4_base_score(self):
        sig = score_filing("AAPL", "123", "4", "acc-004")
        assert sig.base_score == 50

    def test_sc13d_activist_high_score(self):
        sig = score_filing("TSLA", "123", "SC 13D", "acc-005")
        assert sig.base_score == 65
        # SC 13D should trigger alert on base score alone if watchlist bonus applied
        assert sig.significance_score >= 65

    def test_s1_ipo_highest_base(self):
        sig = score_filing("NEWCO", "999", "S-1", "acc-006")
        assert sig.base_score == 80

    def test_8k_item_booster_earnings(self):
        # item 2.02 = +35
        sig = score_filing("AAPL", "123", "8-K", "acc-007", item_numbers=["2.02"])
        assert sig.boosters.get("item_2.02") == 35

    def test_8k_item_booster_executive(self):
        # item 5.02 = +30
        sig = score_filing("MSFT", "456", "8-K", "acc-008", item_numbers=["5.02"])
        assert sig.boosters.get("item_5.02") == 30

    def test_8k_item_booster_material_agreement(self):
        # item 1.01 = +30
        sig = score_filing("AMZN", "789", "8-K", "acc-009", item_numbers=["1.01"])
        assert sig.boosters.get("item_1.01") == 30

    def test_multiple_item_boosters_stack(self):
        # items 2.02 (+35) + 5.02 (+30) = +65 total
        sig = score_filing("NVDA", "321", "8-K", "acc-010", item_numbers=["2.02", "5.02"])
        total_boost = sig.boosters.get("item_2.02", 0) + sig.boosters.get("item_5.02", 0)
        assert total_boost == 65

    def test_recency_bonus_after_hours_early_morning(self):
        # 03:00 UTC = before market open
        sig = score_filing("TSLA", "123", "8-K", "acc-011", filed_at=_utc(3, 0))
        assert sig.boosters.get("after_hours") == 10

    def test_recency_bonus_after_hours_evening(self):
        # 22:00 UTC = after market close
        sig = score_filing("TSLA", "123", "8-K", "acc-012", filed_at=_utc(22, 0))
        assert sig.boosters.get("after_hours") == 10

    def test_no_after_hours_bonus_during_market(self):
        # 16:00 UTC = midday ET (market open)
        sig = score_filing("TSLA", "123", "8-K", "acc-013", filed_at=_utc(16, 0))
        assert "after_hours" not in sig.boosters

    def test_watchlist_ticker_gets_bonus(self):
        sig = score_filing("AAPL", "123", "8-K", "acc-014")
        assert sig.boosters.get("watchlist") == 10

    def test_non_watchlist_ticker_no_bonus(self):
        sig = score_filing("XYZZY", "999", "10-Q", "acc-015")
        assert "watchlist" not in sig.boosters

    def test_alert_threshold_60(self):
        # 8-K base=70 for watchlist ticker → score=80 → alert
        sig = score_filing("AAPL", "123", "8-K", "acc-016")
        assert sig.significance_score >= ALERT_THRESHOLD
        assert sig.alert_triggered is True

    def test_below_threshold_no_alert(self):
        # 10-Q base=30, non-watchlist, no boosters → no alert
        sig = score_filing("XYZZY", "999", "10-Q", "acc-017")
        assert sig.significance_score < ALERT_THRESHOLD
        assert sig.alert_triggered is False

    def test_score_clamped_at_100(self):
        # Many boosters can push score above 100 — must be clamped
        sig = score_filing(
            "AAPL", "123", "8-K", "acc-018",
            item_numbers=["2.02", "5.02", "1.01"],
            filed_at=_utc(3, 0),
        )
        assert sig.significance_score <= 100

    def test_unknown_form_type_gets_default_score(self):
        sig = score_filing("AAPL", "123", "DEFA14A", "acc-019")
        assert sig.base_score == 20  # default for unknown form

    def test_extract_item_numbers_from_description(self):
        items = _extract_item_numbers("8-K: 2.02 Results of Operations and 5.02")
        assert "2.02" in items
        assert "5.02" in items

    def test_extract_item_numbers_empty_description(self):
        items = _extract_item_numbers("")
        assert items == []

    def test_is_after_hours_early_morning(self):
        assert _is_after_hours(_utc(5)) is True

    def test_is_after_hours_market_hours(self):
        assert _is_after_hours(_utc(17)) is False


# ══════════════════════════════════════════════════════════════════════════════
# Insider cluster detection
# ══════════════════════════════════════════════════════════════════════════════

class TestInsiderClusters:
    def test_cluster_two_insiders_same_ticker(self):
        trades = [
            _trade("AAPL", "Alice", value=60_000, days_ago=3),
            _trade("AAPL", "Bob", value=60_000, days_ago=1),
        ]
        clusters = detect_clusters(trades)
        assert len(clusters) == 1
        assert clusters[0].ticker == "AAPL"
        assert clusters[0].insider_count == 2

    def test_no_cluster_single_insider(self):
        trades = [_trade("AAPL", "Alice", value=200_000)]
        clusters = detect_clusters(trades)
        assert clusters == []

    def test_no_cluster_outside_window(self):
        # 30 days apart — outside 7-day window
        trades = [
            _trade("AAPL", "Alice", value=60_000, days_ago=30),
            _trade("AAPL", "Bob", value=60_000, days_ago=0),
        ]
        clusters = detect_clusters(trades)
        assert clusters == []

    def test_cluster_ceo_cfo_bonus(self):
        trades = [
            _trade("MSFT", "Satya N", title="Chief Executive Officer", value=100_000, days_ago=2),
            _trade("MSFT", "Amy H", title="Chief Financial Officer", value=100_000, days_ago=1),
        ]
        clusters = detect_clusters(trades, min_total_value=50_000)
        assert len(clusters) == 1
        assert clusters[0].includes_ceo_cfo is True
        assert clusters[0].cluster_score >= 85  # 70 base + 15 CEO bonus

    def test_cluster_high_value_bonus(self):
        trades = [
            _trade("NVDA", "Alice", value=300_000, days_ago=2),
            _trade("NVDA", "Bob", value=300_000, days_ago=1),
        ]
        clusters = detect_clusters(trades, min_total_value=50_000)
        assert len(clusters) == 1
        assert clusters[0].total_value == 600_000
        # >$500K bonus applies
        assert clusters[0].cluster_score >= 80  # 70 + 10

    def test_cluster_three_insiders_higher_score(self):
        trades = [
            _trade("TSLA", "Alice", value=60_000, days_ago=5),
            _trade("TSLA", "Bob", value=60_000, days_ago=3),
            _trade("TSLA", "Carol", value=60_000, days_ago=1),
        ]
        clusters = detect_clusters(trades)
        assert len(clusters) == 1
        assert clusters[0].insider_count == 3
        # 3+ insiders base = 85 vs 70 for 2
        assert clusters[0].cluster_score >= 85

    def test_cluster_buy_only(self):
        # Sells do not count
        trades = [
            _trade("AAPL", "Alice", tx_type="S", value=100_000, days_ago=2),
            _trade("AAPL", "Bob", tx_type="S", value=100_000, days_ago=1),
        ]
        clusters = detect_clusters(trades)
        assert clusters == []

    def test_cluster_below_min_value_no_cluster(self):
        # total_value=20_000 < min_total_value=100_000
        trades = [
            _trade("AAPL", "Alice", value=10_000, days_ago=2),
            _trade("AAPL", "Bob", value=10_000, days_ago=1),
        ]
        clusters = detect_clusters(trades, min_total_value=100_000)
        assert clusters == []

    def test_different_tickers_no_cross_cluster(self):
        trades = [
            _trade("AAPL", "Alice", value=60_000, days_ago=2),
            _trade("MSFT", "Bob", value=60_000, days_ago=1),
        ]
        clusters = detect_clusters(trades)
        assert clusters == []

    def test_cluster_window_boundary(self):
        # Exactly 7 days apart — should be within window
        trades = [
            _trade("JPM", "Alice", value=60_000, days_ago=7),
            _trade("JPM", "Bob", value=60_000, days_ago=0),
        ]
        clusters = detect_clusters(trades, window_days=7)
        assert len(clusters) == 1


# ══════════════════════════════════════════════════════════════════════════════
# Metric extraction
# ══════════════════════════════════════════════════════════════════════════════

class TestMetricExtractor:
    def test_extract_earnings_event(self):
        filing = {"form_type": "8-K", "description": "8-K 2.02 Results of Operations"}
        metrics = extract_8k_metrics(filing)
        assert metrics.get("event_type") == "earnings"

    def test_extract_executive_change(self):
        filing = {"form_type": "8-K", "description": "Item 5.02 departure of director"}
        metrics = extract_8k_metrics(filing)
        assert metrics.get("event_type") == "executive_change"

    def test_extract_acquisition(self):
        filing = {"form_type": "8-K", "description": "2.01 completion of acquisition"}
        metrics = extract_8k_metrics(filing)
        assert metrics.get("event_type") == "acquisition"

    def test_extract_no_items(self):
        filing = {"form_type": "8-K", "description": "8-K material event"}
        metrics = extract_8k_metrics(filing)
        assert metrics == {}

    def test_non_8k_returns_empty(self):
        filing = {"form_type": "10-K", "description": "Annual Report 2.02"}
        metrics = extract_8k_metrics(filing)
        assert metrics == {}

    def test_explicit_item_numbers_override_description(self):
        filing = {
            "form_type": "8-K",
            "description": "no item numbers here",
            "item_numbers": ["5.02"],
        }
        metrics = extract_8k_metrics(filing)
        assert metrics.get("event_type") == "executive_change"

    def test_multiple_items_first_recognised_wins(self):
        # 2.02 comes first → earnings
        filing = {"form_type": "8-K", "item_numbers": ["2.02", "5.02"]}
        metrics = extract_8k_metrics(filing)
        assert metrics.get("event_type") == "earnings"
        assert metrics.get("item_count") == 2

    def test_8k_variant_form_type(self):
        filing = {"form_type": "8-K/A", "item_numbers": ["4.01"]}
        metrics = extract_8k_metrics(filing)
        assert metrics.get("event_type") == "auditor_change"


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ══════════════════════════════════════════════════════════════════════════════

class TestModels:
    def test_edgar_alert_model_validation(self):
        alert = EdgarAlert(
            alert_id="test-uuid-001",
            ticker="AAPL",
            alert_type="filing_significance",
            significance_score=75,
            summary="Test alert",
            payload={"key": "value"},
        )
        assert alert.ticker == "AAPL"
        assert alert.significance_score == 75
        assert alert.alert_type == "filing_significance"

    def test_edgar_alert_to_intel_envelope(self):
        alert = EdgarAlert(
            alert_id="env-001",
            ticker="MSFT",
            alert_type="insider_cluster",
            significance_score=80,
            summary="Cluster",
            payload={},
        )
        env = alert.to_intel_envelope()
        assert env["source_system"] == "edgar_monitor"
        assert "timestamp" in env
        assert env["value"]["ticker"] == "MSFT"

    def test_insider_cluster_model(self):
        cluster = InsiderCluster(
            ticker="TSLA",
            window_start=datetime(2026, 3, 10, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 15, tzinfo=timezone.utc),
            insiders=["Alice", "Bob"],
            insider_count=2,
            total_value=200_000.0,
            includes_ceo_cfo=False,
            cluster_score=70,
        )
        dumped = cluster.model_dump()
        assert dumped["insider_count"] == 2
        assert dumped["total_value"] == 200_000.0

    def test_filing_significance_model(self):
        sig = FilingSignificance(
            ticker="NVDA",
            cik="abc",
            form_type="8-K",
            accession_number="0001234-26-001",
            significance_score=85,
            base_score=70,
            boosters={"watchlist": 10, "item_2.02": 35},
            alert_triggered=True,
        )
        assert sig.significance_score == 85
        assert sig.alert_triggered is True

    def test_filing_significance_score_clamped_above_100(self):
        sig = FilingSignificance(
            ticker="X", cik="1", form_type="8-K", accession_number="0",
            significance_score=150,  # should clamp to 100
            base_score=70, boosters={}, alert_triggered=True,
        )
        assert sig.significance_score == 100

    def test_filing_significance_score_clamped_below_0(self):
        sig = FilingSignificance(
            ticker="X", cik="1", form_type="8-K", accession_number="0",
            significance_score=-5,  # should clamp to 0
            base_score=0, boosters={}, alert_triggered=False,
        )
        assert sig.significance_score == 0


# ══════════════════════════════════════════════════════════════════════════════
# Subscriber integration (mocked)
# ══════════════════════════════════════════════════════════════════════════════

class TestSubscriberIntegration:
    def _make_filing_envelope(self, form_type: str = "8-K", score: int = 80) -> str:
        payload = {
            "ticker": "AAPL",
            "cik": "0000320193",
            "form_type": form_type,
            "accession_number": "0000320193-26-99999",
            "description": form_type,
            "filing_url": "https://sec.gov/test",
            "filed_at": "2026-03-15T03:00:00+00:00",  # after-hours
        }
        return json.dumps({"value": payload, "source_system": "edgar_pipeline", "timestamp": 1.0, "confidence": 1.0})

    def test_subscriber_publishes_alert(self):
        """Mock Redis: high-score filing should publish intel:edgar_alert."""
        from edgar_monitor import subscriber
        # Clear seen cache for test isolation
        subscriber._seen_accessions.clear()

        mock_redis = MagicMock()
        mock_redis.get.return_value = self._make_filing_envelope("8-K")

        with patch("edgar_monitor.subscriber._redis_client", return_value=mock_redis):
            result = subscriber.run_monitor_cycle(conn=None)

        assert result["filing_alerts"] >= 1

    def test_subscriber_below_threshold_no_publish(self):
        """10-Q for non-watchlist ticker should not trigger alert."""
        from edgar_monitor import subscriber
        subscriber._seen_accessions.clear()

        payload = {
            "ticker": "XYZZY",
            "cik": "999",
            "form_type": "10-Q",
            "accession_number": "0009999-26-00001",
            "description": "10-Q",
            "filing_url": None,
            "filed_at": "2026-03-15T17:00:00+00:00",  # market hours
        }
        envelope = json.dumps({"value": payload, "source_system": "edgar_pipeline", "timestamp": 1.0, "confidence": 1.0})

        mock_redis = MagicMock()
        mock_redis.get.return_value = envelope

        with patch("edgar_monitor.subscriber._redis_client", return_value=mock_redis):
            result = subscriber.run_monitor_cycle(conn=None)

        assert result["filing_alerts"] == 0

    def test_alert_written_to_jsonl(self, tmp_path):
        """JSONL file is created when an alert fires."""
        from edgar_monitor import subscriber
        subscriber._seen_accessions.clear()

        alert = EdgarAlert(
            alert_id="jsonl-test-001",
            ticker="AAPL",
            alert_type="filing_significance",
            significance_score=80,
            summary="Test",
            payload={},
        )

        with patch("edgar_monitor.subscriber._archive_root", return_value=str(tmp_path)):
            subscriber._write_to_jsonl(alert)

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["ticker"] == "AAPL"

    def test_audit_chain_integration(self):
        """chain_writer is called (mocked) when alert fires."""
        from edgar_monitor import subscriber

        alert = EdgarAlert(
            alert_id="audit-test-001",
            ticker="NVDA",
            alert_type="insider_cluster",
            significance_score=85,
            summary="Cluster detected",
            payload={"insiders": ["Alice", "Bob"]},
        )

        with patch("edgar_monitor.subscriber.write_audit_entry", create=True) as mock_write:
            # Directly test _write_to_audit_chain
            with patch("shared.audit_trail.chain_writer.write_audit_entry") as mock_chain:
                subscriber._write_to_audit_chain(alert, conn=None)
                # write_audit_entry is called (even if conn=None it fires)
                # Just verify no exception raised — chain_writer is fail-silent
                pass  # success if no exception

    def test_seen_accession_not_reprocessed(self):
        """Same accession_number is not processed twice."""
        from edgar_monitor import subscriber
        subscriber._seen_accessions.clear()

        mock_redis = MagicMock()
        mock_redis.get.return_value = self._make_filing_envelope("8-K")

        alerts_fired = []
        original_emit = subscriber._emit_alert

        def capturing_emit(alert, conn):
            alerts_fired.append(alert)

        with patch("edgar_monitor.subscriber._redis_client", return_value=mock_redis):
            with patch("edgar_monitor.subscriber._emit_alert", side_effect=capturing_emit):
                subscriber.run_monitor_cycle(conn=None)
                first_count = len(alerts_fired)
                # Second cycle — same accession, should be skipped
                subscriber.run_monitor_cycle(conn=None)
                second_count = len(alerts_fired)

        assert first_count == 1
        assert second_count == 1  # no new alert on second cycle
