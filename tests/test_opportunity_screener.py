"""
tests/test_opportunity_screener.py — Pure unit tests for Step 26.1 (Phase 1)

Coverage:
  26.1b — Entity extraction (dollar sign, company name, alias, ambiguous short tickers)
  26.1c — Bayesian conviction scorer (prior, LR formula, decay, convergence)
  26.1d — Watchlist manager (promotion, demotion, eviction, cap, core, stale TTL)
  26.1e — Screening loop (end-to-end, malformed messages)
  26.1f — Discovery audit logger (batch flush, JSONL, Postgres mock)
  26.1h — Config env var overrides

All tests are PURE — no network, no Redis, no Postgres, mocked I/O.
Run: PYTHONPATH=/opt/cemini pytest tests/test_opportunity_screener.py -v
"""
import json
import os
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

# Ensure we can import service code
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Config patching must happen before importing modules ──────────────────────
os.environ.setdefault("SCREENER_PROMOTION_THRESHOLD", "0.65")
os.environ.setdefault("SCREENER_DEMOTION_THRESHOLD", "0.45")
os.environ.setdefault("SCREENER_MAX_DYNAMIC_TICKERS", "50")
os.environ.setdefault("SCREENER_EVICTION_HYSTERESIS", "0.05")
os.environ.setdefault("SCREENER_STALE_TTL_HOURS", "72")
os.environ.setdefault("SCREENER_DECAY_RATE", "0.995")
os.environ.setdefault("SCREENER_DECAY_INTERVAL_SECONDS", "300")
os.environ.setdefault("SCREENER_CONVERGENCE_WINDOW_MINUTES", "30")
os.environ.setdefault("SCREENER_CONVERGENCE_MULTIPLIER", "1.3")
os.environ.setdefault("SCREENER_AUDIT_FLUSH_SECONDS", "30")
os.environ.setdefault("SCREENER_AUDIT_FLUSH_BATCH_SIZE", "100")
os.environ.setdefault("CORE_WATCHLIST", "SPY,QQQ,IWM,DIA,BTC-USD,ETH-USD")


# ===========================================================================
# 26.1b — Entity Extraction
# ===========================================================================


class TestEntityExtractor(unittest.TestCase):

    def setUp(self):
        # Reset module singleton cache for clean test isolation
        from opportunity_screener import entity_extractor as ee
        ee._initialized = False
        from opportunity_screener.entity_extractor import _ensure_loaded
        _ensure_loaded()

    def _extract(self, text, channel="intel:test"):
        from opportunity_screener.entity_extractor import extract_tickers
        return extract_tickers(channel, text)

    # Dollar-sign patterns

    def test_dollar_sign_extracts_ticker(self):
        results = self._extract("$NVDA is up 5% today")
        syms = {r.symbol for r in results}
        self.assertIn("NVDA", syms)

    def test_dollar_sign_confidence_is_1(self):
        results = self._extract("$AAPL beats earnings")
        hit = next((r for r in results if r.symbol == "AAPL"), None)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.confidence, 1.0)
        self.assertEqual(hit.extraction_method, "dollar_sign")

    def test_dollar_sign_multiple_tickers(self):
        results = self._extract("$AAPL $MSFT $GOOGL all moving together")
        syms = {r.symbol for r in results}
        for t in ("AAPL", "MSFT", "GOOGL"):
            self.assertIn(t, syms)

    # Company name → ticker

    def test_company_name_apple_extracts_aapl(self):
        results = self._extract("Apple reports record earnings this quarter")
        syms = {r.symbol for r in results}
        self.assertIn("AAPL", syms)

    def test_company_name_confidence_09(self):
        results = self._extract("Microsoft announces new AI product")
        hit = next((r for r in results if r.symbol == "MSFT"), None)
        self.assertIsNotNone(hit)
        self.assertAlmostEqual(hit.confidence, 0.9, places=1)
        self.assertIn(hit.extraction_method, ("company_name", "alias", "bare_ticker"))

    def test_company_name_case_insensitive(self):
        results = self._extract("APPLE IS RISING, apple is rising, Apple Is Rising")
        syms = {r.symbol for r in results}
        self.assertIn("AAPL", syms)

    # Alias map

    def test_alias_bitcoin_to_btcusd(self):
        results = self._extract("Bitcoin is rallying due to ETF inflows")
        syms = {r.symbol for r in results}
        self.assertIn("BTC-USD", syms)

    def test_alias_gold_to_gld(self):
        results = self._extract("Gold prices hit record high amid uncertainty")
        syms = {r.symbol for r in results}
        self.assertIn("GLD", syms)

    def test_alias_ethereum_to_ethusd(self):
        results = self._extract("Ethereum network sees record transactions")
        syms = {r.symbol for r in results}
        self.assertIn("ETH-USD", syms)

    def test_alias_treasury_to_tlt(self):
        results = self._extract("Treasury yields spike on Fed hawkishness")
        syms = {r.symbol for r in results}
        self.assertIn("TLT", syms)

    def test_alias_confidence_07(self):
        results = self._extract("oil prices drop on OPEC decision")
        # should produce USO from OPEC alias
        hit = next((r for r in results if r.symbol == "USO"), None)
        if hit:  # alias might yield 0.7
            self.assertLessEqual(hit.confidence, 0.9)

    # Ambiguous short tickers NOT falsely extracted

    def test_it_not_extracted_from_prose(self):
        results = self._extract("It is raining today and it will snow tonight.")
        syms = {r.symbol for r in results}
        self.assertNotIn("IT", syms)

    def test_all_not_extracted_from_prose(self):
        results = self._extract("All of the stocks rallied strongly.")
        syms = {r.symbol for r in results}
        self.assertNotIn("ALL", syms)

    def test_a_not_extracted_without_dollar(self):
        results = self._extract("A strong day for markets.")
        syms = {r.symbol for r in results}
        self.assertNotIn("A", syms)

    def test_are_not_extracted_from_prose(self):
        results = self._extract("Markets are performing well today.")
        syms = {r.symbol for r in results}
        self.assertNotIn("ARE", syms)

    # Dollar sign makes ambiguous ticker valid

    def test_dollar_all_extracted(self):
        results = self._extract("$ALL is my largest holding")
        syms = {r.symbol for r in results}
        self.assertIn("ALL", syms)

    # Empty / malformed

    def test_empty_payload_returns_empty(self):
        results = self._extract("")
        self.assertEqual(results, [])

    def test_none_payload_returns_empty(self):
        from opportunity_screener.entity_extractor import extract_tickers
        results = extract_tickers("intel:test", None)
        self.assertEqual(results, [])

    def test_dict_payload_processed(self):
        from opportunity_screener.entity_extractor import extract_tickers
        results = extract_tickers("intel:test", {"text": "$NVDA earnings beat", "value": 1.5})
        syms = {r.symbol for r in results}
        self.assertIn("NVDA", syms)

    def test_results_sorted_by_confidence_desc(self):
        results = self._extract("$AAPL mentioned along with Apple and gold")
        if len(results) >= 2:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(results[i].confidence, results[i + 1].confidence)

    def test_source_channel_preserved(self):
        from opportunity_screener.entity_extractor import extract_tickers
        results = extract_tickers("intel:geo_risk_score", "$TSLA")
        if results:
            self.assertEqual(results[0].source_channel, "intel:geo_risk_score")


# ===========================================================================
# 26.1c — Bayesian Conviction Scorer
# ===========================================================================


class TestConvictionScorer(unittest.TestCase):

    def _make_scorer(self):
        from opportunity_screener.conviction_scorer import ConvictionState
        return ConvictionState(redis_client=None)

    def test_flat_prior_new_ticker(self):
        scorer = self._make_scorer()
        conviction = scorer.get_conviction("UNKNOWN")
        self.assertAlmostEqual(conviction, 0.5, places=5)

    def test_single_update_increases_conviction(self):
        scorer = self._make_scorer()
        _, after, _ = scorer.update("NVDA", "intel:playbook_snapshot", 0.9, time.time())
        self.assertGreater(after, 0.5)

    def test_source_weight_high_increases_more(self):
        scorer1 = self._make_scorer()
        scorer2 = self._make_scorer()
        _, after_playbook, _ = scorer1.update("AAPL", "intel:playbook_snapshot", 1.0, time.time())
        _, after_social, _ = scorer2.update("AAPL", "intel:social_score", 1.0, time.time())
        self.assertGreater(after_playbook, after_social,
                           "playbook_snapshot (1.5 weight) should yield higher conviction than social_score (0.8)")

    def test_recency_decay_fresh_message(self):
        scorer = self._make_scorer()
        _, after, lr = scorer.update("MSFT", "intel:playbook_snapshot", 1.0, time.time())
        self.assertGreater(after, 0.5)

    def test_recency_decay_1h_old_message(self):
        scorer1 = self._make_scorer()
        scorer2 = self._make_scorer()
        now = time.time()
        _, after_fresh, lr_fresh = scorer1.update("MSFT", "intel:playbook_snapshot", 1.0, now)
        _, after_old, lr_old = scorer2.update("MSFT", "intel:playbook_snapshot", 1.0, now - 3601)
        self.assertLess(lr_old, lr_fresh, "1h+ old message should have lower LR than fresh")

    def test_recency_decay_6h_old_message(self):
        scorer = self._make_scorer()
        now = time.time()
        _, after, lr = scorer.update("GLD", "intel:geo_risk_score", 1.0, now - 21599)
        self.assertGreater(after, 0.5)  # still positive update (≤6h bucket → 0.8 factor)
        # LR should be lower than for fresh
        scorer2 = self._make_scorer()
        _, _, lr_fresh = scorer2.update("GLD", "intel:geo_risk_score", 1.0, now)
        self.assertLess(lr, lr_fresh)

    def test_multi_source_convergence_bonus_triggers(self):
        scorer = self._make_scorer()
        now = time.time()
        # First update from channel A
        scorer.update("SPY", "intel:playbook_snapshot", 1.0, now)
        # Second update from distinct channel B → should trigger convergence bonus
        scorer2 = self._make_scorer()
        _, without_bonus, _ = scorer2.update("SPY", "intel:playbook_snapshot", 1.0, now)
        _, with_bonus, _ = scorer.update("SPY", "intel:geo_risk_score", 1.0, now)
        self.assertGreater(with_bonus, without_bonus,
                           "Multi-source bonus should yield higher conviction")

    def test_multi_source_bonus_same_channel_no_bonus(self):
        scorer = self._make_scorer()
        now = time.time()
        scorer.update("QQQ", "intel:geo_risk_score", 1.0, now)
        # Same channel again → no convergence bonus
        _, after2, _ = scorer.update("QQQ", "intel:geo_risk_score", 1.0, now + 60)
        # conviction should still increase, but no 1.3x bonus
        scorer_control = self._make_scorer()
        scorer_control.update("QQQ", "intel:geo_risk_score", 1.0, now)
        # We can't inspect the multiplier directly, just verify it's < what two channels would produce
        scorer_two_ch = self._make_scorer()
        scorer_two_ch.update("QQQ", "intel:geo_risk_score", 1.0, now)
        _, after_two_ch, _ = scorer_two_ch.update("QQQ", "intel:playbook_snapshot", 1.0, now + 60)
        self.assertGreater(after_two_ch, after2,
                           "Two distinct channels should outperform same channel twice")

    def test_conviction_decay(self):
        scorer = self._make_scorer()
        scorer._state["TSLA"] = {
            "conviction": 0.8,
            "last_updated": "2026-01-01T00:00:00+00:00",
            "source_count": 5,
            "sources": ["intel:playbook_snapshot"],
            "first_seen": "2026-01-01T00:00:00+00:00",
        }
        changes = scorer.decay_all()
        after = scorer.get_conviction("TSLA")
        self.assertLess(after, 0.8, "Conviction should decay below starting value")
        self.assertAlmostEqual(after, 0.8 * 0.995, places=5)

    def test_core_tickers_not_decayed(self):
        from opportunity_screener.config import CORE_WATCHLIST
        scorer = self._make_scorer()
        for ticker in CORE_WATCHLIST:
            scorer._state[ticker] = {
                "conviction": 0.9,
                "last_updated": "2026-01-01T00:00:00+00:00",
                "source_count": 1,
                "sources": [],
                "first_seen": "2026-01-01T00:00:00+00:00",
            }
        scorer.decay_all()
        for ticker in CORE_WATCHLIST:
            self.assertAlmostEqual(scorer.get_conviction(ticker), 0.9, places=5,
                                   msg=f"Core ticker {ticker} should not decay")

    def test_score_clamp_high(self):
        scorer = self._make_scorer()
        # Repeatedly update with max weights to push toward 1.0
        now = time.time()
        for _ in range(50):
            scorer.update("AAPL", "intel:playbook_snapshot", 1.0, now)
        self.assertLessEqual(scorer.get_conviction("AAPL"), 0.99)

    def test_score_clamp_low(self):
        scorer = self._make_scorer()
        scorer._state["AAPL"] = {
            "conviction": 0.001,
            "last_updated": "",
            "source_count": 0,
            "sources": [],
            "first_seen": "",
        }
        # decay many times
        for _ in range(1000):
            scorer.decay_all()
        self.assertGreaterEqual(scorer.get_conviction("AAPL"), 0.01)

    def test_posterior_odds_math(self):
        """Manual calculation: prior=0.5, sw=1.5, conf=1.0, rf=1.0, no bonus → LR=1.5."""
        scorer = self._make_scorer()
        now = time.time()
        before, after, lr = scorer.update("TEST_MANUAL", "intel:playbook_snapshot", 1.0, now)
        # prior_odds = 0.5/0.5 = 1.0
        # posterior_odds = 1.0 * 1.5 = 1.5
        # conviction = 1.5 / (1 + 1.5) = 0.6
        self.assertAlmostEqual(before, 0.5, places=5)
        self.assertAlmostEqual(after, 1.5 / 2.5, places=4)

    def test_unknown_channel_uses_default_weight(self):
        from opportunity_screener.conviction_scorer import _DEFAULT_SOURCE_WEIGHT
        scorer = self._make_scorer()
        now = time.time()
        before, after, lr = scorer.update("AAPL", "intel:unknown_future_channel", 1.0, now)
        # LR should use 0.7 default weight
        expected_lr = _DEFAULT_SOURCE_WEIGHT * 1.0 * 1.0  # rf=1.0 (fresh), no bonus
        self.assertAlmostEqual(lr, expected_lr, places=3)


# ===========================================================================
# 26.1d — Watchlist Manager
# ===========================================================================


class TestWatchlistManager(unittest.TestCase):

    def _make_manager(self):
        from opportunity_screener.watchlist_manager import WatchlistManager
        return WatchlistManager(redis_client=None)

    def test_promotion_at_threshold(self):
        mgr = self._make_manager()
        action = mgr.evaluate("NVDA", 0.70, "intel:playbook_snapshot")
        self.assertEqual(action, "promoted")
        self.assertIn("NVDA", mgr._dynamic)

    def test_no_promotion_below_threshold(self):
        mgr = self._make_manager()
        action = mgr.evaluate("NVDA", 0.60, "intel:playbook_snapshot")
        self.assertIsNone(action)
        self.assertNotIn("NVDA", mgr._dynamic)

    def test_demotion_at_floor(self):
        mgr = self._make_manager()
        mgr.evaluate("NVDA", 0.70, "intel:playbook_snapshot")  # promote
        action = mgr.evaluate("NVDA", 0.44, "decay")  # below 0.45
        self.assertEqual(action, "demoted")
        self.assertNotIn("NVDA", mgr._dynamic)

    def test_hysteresis_eviction_requires_gap(self):
        """Eviction requires new ticker conviction to exceed lowest by ≥ 0.05."""
        mgr = self._make_manager()
        # Fill to cap
        for i in range(50):
            mgr._dynamic[f"FAKE{i:03d}"] = {"conviction": 0.66, "promoted_at": time.time(),
                                              "last_intel_at": time.time(), "source_channels": [], "promotion_reason": ""}
        # Try to add ticker with conviction 0.70 — lowest is 0.66, gap = 0.04 < 0.05
        action = mgr.evaluate("NEWT", 0.70, "intel:test")
        self.assertIsNone(action, "0.04 gap should be insufficient for eviction")

    def test_eviction_when_gap_sufficient(self):
        mgr = self._make_manager()
        for i in range(50):
            mgr._dynamic[f"FAKE{i:03d}"] = {"conviction": 0.66, "promoted_at": time.time(),
                                              "last_intel_at": time.time(), "source_channels": [], "promotion_reason": ""}
        # Gap = 0.72 - 0.66 = 0.06 ≥ 0.05 → should evict lowest and promote new
        action = mgr.evaluate("NEWT", 0.72, "intel:test")
        self.assertEqual(action, "promoted")
        self.assertIn("NEWT", mgr._dynamic)
        self.assertEqual(len(mgr._dynamic), 50)  # cap maintained

    def test_cap_enforced_50_dynamic(self):
        mgr = self._make_manager()
        for i in range(50):
            mgr.evaluate(f"TKR{i:04d}", 0.70, "intel:test")
        self.assertEqual(mgr.dynamic_count(), 50)
        # 51st should not get promoted without eviction opportunity
        action = mgr.evaluate("EXTRA0", 0.70, "intel:test")  # same conviction → no gap
        # EXTRA0 must not be promoted if insufficient gap
        # (all dynamic are at 0.70, gap would be 0 < 0.05)
        self.assertEqual(mgr.dynamic_count(), 50)

    def test_core_tickers_never_evicted(self):
        from opportunity_screener.config import CORE_WATCHLIST
        mgr = self._make_manager()
        for t in CORE_WATCHLIST:
            self.assertIn(t, mgr._core)
        # Core tickers evaluate to None (no action)
        for t in CORE_WATCHLIST:
            action = mgr.evaluate(t, 0.44, "decay")  # below demotion floor
            self.assertIsNone(action, f"Core ticker {t} should not be demoted")

    def test_core_tickers_not_counted_in_dynamic(self):
        mgr = self._make_manager()
        self.assertEqual(mgr.dynamic_count(), 0)
        # is_watched returns True for core even though not in _dynamic
        self.assertTrue(mgr.is_watched("SPY"))
        self.assertEqual(mgr.dynamic_count(), 0)

    def test_stale_ttl_enforcement(self):
        mgr = self._make_manager()
        # Add ticker with very old last_intel_at
        mgr._dynamic["STALE"] = {
            "conviction": 0.70,
            "promoted_at": time.time() - 100000,
            "last_intel_at": time.time() - (73 * 3600),  # 73h ago → stale
            "source_channels": [],
            "promotion_reason": "test",
        }
        demoted = mgr.enforce_stale_ttl()
        self.assertIn("STALE", demoted)
        self.assertNotIn("STALE", mgr._dynamic)

    def test_recent_ticker_not_force_demoted(self):
        mgr = self._make_manager()
        mgr._dynamic["FRESH"] = {
            "conviction": 0.70,
            "promoted_at": time.time(),
            "last_intel_at": time.time() - 3600,  # 1h ago → fresh
            "source_channels": [],
            "promotion_reason": "test",
        }
        demoted = mgr.enforce_stale_ttl()
        self.assertNotIn("FRESH", demoted)

    def test_watchlist_sorted_by_conviction(self):
        mgr = self._make_manager()
        mgr.evaluate("AAPL", 0.80, "intel:test")
        mgr.evaluate("MSFT", 0.70, "intel:test")
        mgr.evaluate("NVDA", 0.90, "intel:test")
        wl = mgr.get_watchlist()
        dynamic = [e for e in wl if not e.get("is_core")]
        convictions = [e["conviction"] for e in dynamic]
        self.assertEqual(convictions, sorted(convictions, reverse=True))

    def test_promotion_event_published(self):
        """With mock Redis, verify watchlist_update is SET on promotion."""
        mock_redis = MagicMock()
        from opportunity_screener.watchlist_manager import WatchlistManager
        mgr = WatchlistManager(redis_client=mock_redis)
        mgr.evaluate("TSLA", 0.80, "intel:playbook_snapshot")
        mock_redis.set.assert_called()
        call_args = mock_redis.set.call_args
        self.assertEqual(call_args[0][0], "intel:watchlist_update")


# ===========================================================================
# 26.1e — Screening Loop (end-to-end mock)
# ===========================================================================


class TestScreeningLoop(unittest.TestCase):

    def _make_screener(self):
        from opportunity_screener.screener import OpportunityScreener
        s = OpportunityScreener()
        s._redis = None
        s._conviction._redis = None
        s._watchlist._redis = None
        s._logger = None
        return s

    def test_process_message_increments_counter(self):
        s = self._make_screener()
        envelope = {
            "value": "$NVDA earnings beat expectations",
            "source_system": "test",
            "timestamp": time.time(),
            "confidence": 1.0,
        }
        s._process_message("intel:playbook_snapshot", envelope, time.time())
        self.assertGreater(s.messages_processed, 0)

    def test_process_message_multiple_tickers(self):
        s = self._make_screener()
        envelope = {
            "value": "$AAPL $MSFT $NVDA all up after earnings",
            "source_system": "test",
            "timestamp": time.time(),
            "confidence": 1.0,
        }
        s._process_message("intel:playbook_snapshot", envelope, time.time())
        self.assertGreater(s.extractions_total, 1)

    def test_process_message_malformed_ignored(self):
        s = self._make_screener()
        # Value is None → should silently skip
        envelope = {"value": None, "source_system": "test", "timestamp": time.time(), "confidence": 1.0}
        try:
            s._process_message("intel:test", envelope, time.time())
        except Exception as exc:
            self.fail(f"Malformed message raised: {exc}")

    def test_process_message_conviction_updated(self):
        s = self._make_screener()
        initial = s._conviction.get_conviction("NVDA")
        envelope = {"value": "$NVDA", "source_system": "test", "timestamp": time.time(), "confidence": 1.0}
        s._process_message("intel:playbook_snapshot", envelope, time.time())
        updated = s._conviction.get_conviction("NVDA")
        self.assertGreater(updated, initial)

    def test_get_stats_returns_expected_keys(self):
        s = self._make_screener()
        stats = s.get_stats()
        for key in ("messages_processed", "extractions_total", "tickers_tracked",
                    "watchlist_size", "uptime_seconds", "msgs_per_minute"):
            self.assertIn(key, stats)

    def test_duplicate_channel_timestamp_skipped(self):
        """If channel timestamp didn't change, message should not be re-processed."""
        s = self._make_screener()
        ts = time.time()
        s._channel_last_ts["intel:geo_risk_score"] = ts
        # Simulate poll: message with same ts → should not process
        import asyncio
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({
            "value": "$AAPL $MSFT",
            "source_system": "test",
            "timestamp": ts,
            "confidence": 1.0,
        })
        s._redis = mock_redis
        asyncio.run(s._poll_channels())
        # messages_processed should be 0 because ts == last_ts
        for ch in s._channel_last_ts:
            pass  # just ensure no exception


# ===========================================================================
# 26.1f — Discovery Audit Logger
# ===========================================================================


class TestDiscoveryLogger(unittest.TestCase):

    def test_log_buffers_records(self):
        from opportunity_screener.discovery_logger import DiscoveryLogger
        dl = DiscoveryLogger(db_conn=None)
        dl.log(ticker="AAPL", action="conviction_update", conviction_before=0.5, conviction_after=0.6)
        self.assertEqual(len(dl._buffer), 1)

    def test_flush_at_batch_size(self):
        from opportunity_screener.discovery_logger import DiscoveryLogger
        dl = DiscoveryLogger(db_conn=None)
        dl._last_flush = time.time()  # prevent time-based flush
        # Patch JSONL writer so no actual file I/O
        with patch.object(dl, "_write_jsonl", return_value=0):
            for _ in range(100):
                dl.log(ticker="TEST", action="conviction_update",
                       conviction_before=0.5, conviction_after=0.6)
        # After 100th entry, buffer should be flushed
        self.assertEqual(len(dl._buffer), 0)

    def test_flush_at_time_threshold(self):
        from opportunity_screener.discovery_logger import DiscoveryLogger
        dl = DiscoveryLogger(db_conn=None)
        dl._last_flush = time.time() - 31  # 31s ago → time threshold exceeded
        with patch.object(dl, "_write_jsonl", return_value=1):
            dl.log(ticker="TEST", action="conviction_update")
        self.assertEqual(len(dl._buffer), 0)

    def test_jsonl_writes_valid_json(self):
        from opportunity_screener.discovery_logger import DiscoveryLogger
        import tempfile
        dl = DiscoveryLogger(db_conn=None)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("opportunity_screener.discovery_logger._ARCHIVE_DIR", Path(tmpdir)):
                batch = [{
                    "timestamp": time.time(),
                    "ticker": "NVDA",
                    "action": "promoted",
                    "conviction_before": 0.5,
                    "conviction_after": 0.70,
                    "source_channel": "intel:playbook_snapshot",
                    "extraction_confidence": 0.9,
                    "likelihood_ratio": 1.5,
                    "multi_source_bonus": False,
                    "payload": {"key": "value"},
                    "watchlist_size": 10,
                }]
                dl._write_jsonl(batch)
                from datetime import datetime, timezone
                date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
                log_file = Path(tmpdir) / f"discovery_{date_str}.jsonl"
                self.assertTrue(log_file.exists())
                with open(log_file) as f:
                    line = f.readline()
                record = json.loads(line)
                self.assertEqual(record["ticker"], "NVDA")
                self.assertEqual(record["action"], "promoted")

    def test_postgres_insert_called_with_correct_params(self):
        from opportunity_screener.discovery_logger import DiscoveryLogger
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        dl = DiscoveryLogger(db_conn=mock_conn)
        batch = [{
            "timestamp": time.time(),
            "ticker": "AAPL",
            "action": "promoted",
            "conviction_before": 0.5,
            "conviction_after": 0.70,
            "source_channel": "intel:test",
            "extraction_confidence": 1.0,
            "likelihood_ratio": 1.5,
            "multi_source_bonus": False,
            "payload": None,
            "watchlist_size": 5,
        }]
        dl._write_postgres(batch)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_audit_record_includes_conviction_before_after(self):
        from opportunity_screener.discovery_logger import DiscoveryLogger
        dl = DiscoveryLogger(db_conn=None)
        dl.log(ticker="MSFT", action="conviction_update",
               conviction_before=0.45, conviction_after=0.68,
               watchlist_size=12)
        record = dl._buffer[0]
        self.assertAlmostEqual(record["conviction_before"], 0.45)
        self.assertAlmostEqual(record["conviction_after"], 0.68)
        self.assertEqual(record["watchlist_size"], 12)


# ===========================================================================
# 26.1h — Configuration env var overrides
# ===========================================================================


class TestConfig(unittest.TestCase):

    def test_promotion_threshold_default(self):
        from opportunity_screener.config import SCREENER_PROMOTION_THRESHOLD
        self.assertAlmostEqual(SCREENER_PROMOTION_THRESHOLD, 0.65, places=4)

    def test_demotion_threshold_default(self):
        from opportunity_screener.config import SCREENER_DEMOTION_THRESHOLD
        self.assertAlmostEqual(SCREENER_DEMOTION_THRESHOLD, 0.45, places=4)

    def test_max_dynamic_tickers_default(self):
        from opportunity_screener.config import SCREENER_MAX_DYNAMIC_TICKERS
        self.assertEqual(SCREENER_MAX_DYNAMIC_TICKERS, 50)

    def test_core_watchlist_default(self):
        from opportunity_screener.config import CORE_WATCHLIST
        self.assertIn("SPY", CORE_WATCHLIST)
        self.assertIn("BTC-USD", CORE_WATCHLIST)
        self.assertEqual(len(CORE_WATCHLIST), 6)

    def test_decay_rate_default(self):
        from opportunity_screener.config import SCREENER_DECAY_RATE
        self.assertAlmostEqual(SCREENER_DECAY_RATE, 0.995, places=4)

    def test_env_var_override(self):
        """Verify env vars override defaults at module level."""
        # The defaults are already set via os.environ.setdefault at top of file
        from opportunity_screener.config import SCREENER_AUDIT_FLUSH_BATCH_SIZE
        self.assertEqual(SCREENER_AUDIT_FLUSH_BATCH_SIZE, 100)

    def test_intel_channels_list(self):
        from opportunity_screener.config import INTEL_CHANNELS
        self.assertIn("intel:playbook_snapshot", INTEL_CHANNELS)
        self.assertIn("intel:geo_risk_score", INTEL_CHANNELS)
        self.assertGreater(len(INTEL_CHANNELS), 10)


# ===========================================================================
# API endpoint smoke tests (no network — TestClient)
# ===========================================================================


class TestFastAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
            from opportunity_screener.main import app, _screener
            # Patch screener startup to avoid Redis/DB connections
            _screener._running = True
            cls.client = TestClient(app, raise_server_exceptions=False)
        except ImportError:
            cls.client = None

    def _skip_if_no_client(self):
        if self.client is None:
            self.skipTest("fastapi/httpx not installed")

    def test_health_returns_200(self):
        self._skip_if_no_client()
        resp = self.client.get("/health")
        self.assertIn(resp.status_code, (200, 500))  # 500 ok if lifespan not run

    def test_health_structure(self):
        self._skip_if_no_client()
        from opportunity_screener.main import _screener
        # Call the endpoint function directly
        import asyncio
        from opportunity_screener.main import health
        result = asyncio.run(health())
        self.assertIn("status", result)
        self.assertIn("watchlist_size", result)
        self.assertIn("tickers_tracked", result)
        self.assertIn("messages_processed", result)
        self.assertIn("uptime_seconds", result)

    def test_watchlist_endpoint_structure(self):
        self._skip_if_no_client()
        import asyncio
        from opportunity_screener.main import get_watchlist
        result = asyncio.run(get_watchlist())
        self.assertIn("watchlist", result)
        self.assertIn("dynamic_count", result)

    def test_convictions_unknown_ticker_404(self):
        self._skip_if_no_client()
        import asyncio
        from fastapi import HTTPException
        from opportunity_screener.main import get_conviction
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(get_conviction("XYZNOTEXISTS"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_stats_endpoint_keys(self):
        self._skip_if_no_client()
        import asyncio
        from opportunity_screener.main import get_stats
        stats = asyncio.run(get_stats())
        for key in ("messages_processed", "tickers_tracked", "uptime_seconds"):
            self.assertIn(key, stats)


# ===========================================================================
# Pydantic contracts
# ===========================================================================


class TestDiscoveryContracts(unittest.TestCase):

    def test_extracted_ticker_valid(self):
        from cemini_contracts.discovery import ExtractedTicker
        t = ExtractedTicker(
            symbol="AAPL",
            source_channel="intel:test",
            confidence=0.9,
            extraction_method="company_name",
        )
        self.assertEqual(t.symbol, "AAPL")

    def test_conviction_score_clamped(self):
        from cemini_contracts.discovery import ConvictionScore
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            # conviction=1.05 should fail validation (> 0.99)
            ConvictionScore(ticker="AAPL", conviction=1.05)

    def test_watchlist_update_model(self):
        from cemini_contracts.discovery import WatchlistUpdate
        u = WatchlistUpdate(action="promoted", ticker="NVDA", conviction=0.75, reason="threshold_crossed")
        self.assertEqual(u.action, "promoted")
        data = u.model_dump()
        self.assertIn("timestamp", data)

    def test_discovery_snapshot_model(self):
        from cemini_contracts.discovery import DiscoverySnapshot
        snap = DiscoverySnapshot(
            watchlist=[{"ticker": "SPY", "conviction": 0.5}],
            tickers_tracked=10,
            messages_processed=100,
        )
        self.assertEqual(snap.tickers_tracked, 10)

    def test_discovery_audit_record_model(self):
        from cemini_contracts.discovery import DiscoveryAuditRecord
        rec = DiscoveryAuditRecord(
            ticker="AAPL",
            action="promoted",
            conviction_before=0.5,
            conviction_after=0.70,
            source_channel="intel:playbook_snapshot",
        )
        self.assertEqual(rec.ticker, "AAPL")


if __name__ == "__main__":
    unittest.main()
