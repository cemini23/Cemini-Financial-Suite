"""tests/test_vector_intelligence.py — Step 29 Vector Intelligence Tests.

All tests are pure: no network, no Postgres, no model loading, mocked I/O.
34 tests covering embedder, vector_store, CRAG retriever, seeder, Pydantic contracts,
and realtime_worker.
"""
from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_FAKE_VEC = [0.1] * 384
_FAKE_VEC2 = [0.2] * 384


def _make_fake_model(dim: int = 384):
    """Return a mock SentenceTransformer that returns fake vectors."""
    import numpy as np

    model = MagicMock()
    model.encode.side_effect = lambda texts, batch_size=64, normalize_embeddings=True: (
        np.array([[0.1] * dim] * len(texts)) if isinstance(texts, list) else np.array([0.1] * dim)
    )
    return model


# ─────────────────────────────────────────────────────────────────────────────
# Embedding tests
# ─────────────────────────────────────────────────────────────────────────────


class TestEmbedder:
    def setup_method(self):
        """Reset the module-level singleton before each test."""
        import intelligence.embedder as emb
        emb.reset_model()

    def test_embed_returns_384_dims(self):
        """embed() should return a list of 384 floats."""
        with patch("intelligence.embedder._get_model", return_value=_make_fake_model()):
            from intelligence.embedder import embed
            result = embed("test text")
        assert isinstance(result, list)
        assert len(result) == 384
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch_multiple_texts(self):
        """embed_batch() returns one vector per input text."""
        with patch("intelligence.embedder._get_model", return_value=_make_fake_model()):
            from intelligence.embedder import embed_batch
            results = embed_batch(["text one", "text two", "text three"])
        assert len(results) == 3
        assert all(len(v) == 384 for v in results)

    def test_embed_batch_empty(self):
        """embed_batch([]) returns an empty list without loading the model."""
        import intelligence.embedder as emb
        assert emb.embed_batch([]) == []

    def test_lazy_loading_not_loaded_at_import(self):
        """Model singleton is None before first embed() call."""
        import intelligence.embedder as emb
        emb.reset_model()
        assert emb.is_model_loaded() is False

    def test_lazy_loading_set_after_embed(self):
        """is_model_loaded() becomes True after a successful embed call."""
        import intelligence.embedder as emb
        fake_model = _make_fake_model()

        # Patch _get_model directly to avoid importing sentence_transformers in CI
        original_get_model = emb._get_model

        def _patched_get():
            emb._model = fake_model
            return fake_model

        emb._get_model = _patched_get
        try:
            emb.embed("hello")
            assert emb.is_model_loaded() is True
        finally:
            emb._get_model = original_get_model


# ─────────────────────────────────────────────────────────────────────────────
# Vector Store tests
# ─────────────────────────────────────────────────────────────────────────────


def _mock_conn(fetchone=None, fetchall=None, rowcount=1):
    """Build a mock psycopg2 connection + cursor hierarchy."""
    cur = MagicMock()
    cur.fetchone.return_value = fetchone if fetchone is not None else (42,)
    cur.fetchall.return_value = fetchall if fetchall is not None else []
    cur.rowcount = rowcount

    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    cursor_cm = MagicMock()
    cursor_cm.__enter__ = MagicMock(return_value=cur)
    cursor_cm.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor_cm
    return conn, cur


class TestVectorStore:
    def _patch_conn(self, conn):
        """Patch _get_conn in vector_store module."""
        return patch("intelligence.vector_store._get_conn", return_value=conn)

    def test_store_embedding_returns_id(self):
        """store_embedding inserts a row and returns its id."""
        conn, cur = _mock_conn(fetchone=(99,))
        with self._patch_conn(conn):
            from intelligence.vector_store import store_embedding
            row_id = store_embedding(
                content="test content",
                embedding=_FAKE_VEC,
                source_type="x_tweet",
                source_id="tweet_123",
                metadata={"author": "user"},
                tickers=["AAPL"],
            )
        assert row_id == 99
        assert cur.execute.called

    def test_store_embedding_with_timestamp(self):
        """store_embedding with explicit timestamp uses the timestamp branch."""
        conn, cur = _mock_conn(fetchone=(7,))
        ts = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
        with self._patch_conn(conn):
            from intelligence.vector_store import store_embedding
            row_id = store_embedding(
                content="content",
                embedding=_FAKE_VEC,
                source_type="intel_message",
                timestamp=ts,
            )
        assert row_id == 7
        # Verify timestamp was in the INSERT params
        call_args = cur.execute.call_args_list
        insert_call = [c for c in call_args if "INSERT" in str(c)][0]
        assert ts in insert_call.args[1]

    def test_store_embeddings_batch_returns_count(self):
        """store_embeddings_batch returns rowcount from execute_values."""
        conn, cur = _mock_conn(rowcount=5)
        records = [
            {"content": f"text {i}", "embedding": _FAKE_VEC, "source_type": "x_tweet", "source_id": str(i)}
            for i in range(5)
        ]
        with (
            self._patch_conn(conn),
            patch("intelligence.vector_store.execute_values") as mock_ev,
        ):
            from intelligence.vector_store import store_embeddings_batch
            n = store_embeddings_batch(records)
        assert mock_ev.called
        assert n == 5

    def test_store_embeddings_batch_empty(self):
        """store_embeddings_batch([]) returns 0 without touching the DB."""
        with patch("intelligence.vector_store._get_conn") as mock_gc:
            from intelligence.vector_store import store_embeddings_batch
            n = store_embeddings_batch([])
        assert n == 0
        mock_gc.assert_not_called()

    def test_search_similar_no_filters(self):
        """search_similar with no filters executes SET LOCAL + SELECT."""
        fake_row = (1, "some content", "x_tweet", "id1", "intel:x", 0.85, '{"a":1}', ["AAPL"], None)
        conn, cur = _mock_conn(fetchall=[fake_row])
        with self._patch_conn(conn):
            from intelligence.vector_store import search_similar
            results = search_similar(_FAKE_VEC, limit=5)
        # SET LOCAL should be first execute call
        first_call = cur.execute.call_args_list[0]
        assert "hnsw.ef_search" in str(first_call)
        assert len(results) == 1
        assert results[0]["similarity_score"] == 0.85
        assert results[0]["source_type"] == "x_tweet"

    def test_search_similar_source_type_filter(self):
        """search_similar with source_type appends source_type = %s to WHERE."""
        conn, cur = _mock_conn(fetchall=[])
        with self._patch_conn(conn):
            from intelligence.vector_store import search_similar
            search_similar(_FAKE_VEC, source_type="gdelt_article")
        sql_call = cur.execute.call_args_list[1]  # second call is the SELECT
        assert "source_type = %s" in sql_call.args[0]
        assert "gdelt_article" in sql_call.args[1]

    def test_search_similar_tickers_filter(self):
        """search_similar with tickers uses the && (overlap) operator."""
        conn, cur = _mock_conn(fetchall=[])
        with self._patch_conn(conn):
            from intelligence.vector_store import search_similar
            search_similar(_FAKE_VEC, tickers=["AAPL", "MSFT"])
        sql_call = cur.execute.call_args_list[1]
        assert "tickers && %s" in sql_call.args[0]

    def test_search_similar_since_filter(self):
        """search_similar with since appends timestamp >= %s to WHERE."""
        conn, cur = _mock_conn(fetchall=[])
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        with self._patch_conn(conn):
            from intelligence.vector_store import search_similar
            search_similar(_FAKE_VEC, since=since)
        sql_call = cur.execute.call_args_list[1]
        assert "timestamp >= %s" in sql_call.args[0]
        assert since in sql_call.args[1]

    def test_search_similar_min_similarity(self):
        """min_similarity is passed as a WHERE param."""
        conn, cur = _mock_conn(fetchall=[])
        with self._patch_conn(conn):
            from intelligence.vector_store import search_similar
            search_similar(_FAKE_VEC, min_similarity=0.75)
        sql_call = cur.execute.call_args_list[1]
        assert 0.75 in sql_call.args[1]

    def test_search_similar_with_market_context_contains_join(self):
        """search_similar_with_market_context SQL includes LATERAL JOIN."""
        conn, cur = _mock_conn(fetchall=[])
        with self._patch_conn(conn):
            from intelligence.vector_store import search_similar_with_market_context
            search_similar_with_market_context(_FAKE_VEC, limit=5)
        sql_call = cur.execute.call_args_list[1]
        assert "LEFT JOIN LATERAL" in sql_call.args[0]
        assert "raw_market_ticks" in sql_call.args[0]

    def test_get_stats_returns_structure(self):
        """get_stats returns dict with expected keys."""
        conn, cur = _mock_conn()
        cur.fetchone.side_effect = [
            (100,),                     # COUNT(*)
            (datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 3, 8, tzinfo=timezone.utc)),
        ]
        cur.fetchall.return_value = [("x_tweet", 80), ("gdelt_article", 20)]

        with self._patch_conn(conn):
            from intelligence.vector_store import get_stats
            stats = get_stats()

        assert stats["total_embeddings"] == 100
        assert "x_tweet" in stats["by_source_type"]
        assert stats["avg_per_day"] > 0
        assert stats["oldest"] is not None
        assert stats["newest"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# CRAG Retriever tests
# ─────────────────────────────────────────────────────────────────────────────


def _make_doc(score: float, content: str = "doc", tid: int = 1) -> dict:
    return {
        "id": tid,
        "content": content,
        "source_type": "x_tweet",
        "source_id": str(tid),
        "source_channel": None,
        "similarity_score": score,
        "metadata": {},
        "tickers": [],
        "timestamp": None,
    }


class TestCRAGRetriever:
    def test_grade_relevant(self):
        """score >= 0.7 → RELEVANT."""
        from intelligence.retriever import _grade
        assert _grade(0.7) == "RELEVANT"
        assert _grade(0.85) == "RELEVANT"
        assert _grade(1.0) == "RELEVANT"

    def test_grade_ambiguous(self):
        """0.5 <= score < 0.7 → AMBIGUOUS."""
        from intelligence.retriever import _grade
        assert _grade(0.5) == "AMBIGUOUS"
        assert _grade(0.65) == "AMBIGUOUS"
        assert _grade(0.699) == "AMBIGUOUS"

    def test_grade_irrelevant(self):
        """score < 0.5 → IRRELEVANT."""
        from intelligence.retriever import _grade
        assert _grade(0.0) == "IRRELEVANT"
        assert _grade(0.49) == "IRRELEVANT"

    def test_all_relevant_high_quality(self):
        """When all retrieved docs are RELEVANT, quality='high'."""
        docs = [_make_doc(0.9, f"doc{i}", i) for i in range(5)]
        with (
            patch("intelligence.retriever.embed", return_value=_FAKE_VEC),
            patch("intelligence.retriever.search_similar", return_value=docs),
        ):
            from intelligence.retriever import retrieve_context
            result = retrieve_context("test query", max_results=5)
        assert result.retrieval_quality == "high"
        assert len(result.contexts) == 5
        assert all(c.grade == "RELEVANT" for c in result.contexts)

    def test_mixed_quality_returns_relevant_first(self):
        """Mix of RELEVANT+AMBIGUOUS → quality='mixed', RELEVANT docs kept."""
        docs = [
            _make_doc(0.9, "relevant doc", 1),
            _make_doc(0.6, "ambiguous doc", 2),
            _make_doc(0.6, "ambiguous doc2", 3),
        ]
        with (
            patch("intelligence.retriever.embed", return_value=_FAKE_VEC),
            patch("intelligence.retriever.search_similar", return_value=docs),
        ):
            from intelligence.retriever import retrieve_context
            result = retrieve_context("test query", max_results=5)
        assert result.retrieval_quality == "mixed"
        assert result.total_relevant == 1
        relevant_contexts = [c for c in result.contexts if c.grade == "RELEVANT"]
        assert len(relevant_contexts) >= 1

    def test_all_irrelevant_insufficient(self):
        """All docs below threshold → quality='insufficient', contexts=[]."""
        docs = [_make_doc(0.3, f"bad{i}", i) for i in range(3)]
        with (
            patch("intelligence.retriever.embed", return_value=_FAKE_VEC),
            patch("intelligence.retriever.search_similar", return_value=docs),
        ):
            from intelligence.retriever import retrieve_context
            result = retrieve_context("test query")
        assert result.retrieval_quality == "insufficient"
        assert result.contexts == []
        assert result.total_relevant == 0

    def test_retrieve_context_error_returns_insufficient(self):
        """Exception in retrieval → graceful fallback to insufficient."""
        with (
            patch("intelligence.retriever.embed", side_effect=RuntimeError("DB down")),
        ):
            from intelligence.retriever import retrieve_context
            result = retrieve_context("test query")
        assert result.retrieval_quality == "insufficient"
        assert result.total_retrieved == 0

    def test_retrieve_context_source_types_filter(self):
        """source_types param causes per-type searches to be merged."""
        docs_a = [_make_doc(0.85, "tweet", 1)]
        docs_b = [_make_doc(0.80, "gdelt", 2)]

        def _fake_search(vec, limit=10, source_type=None, **kwargs):
            if source_type == "x_tweet":
                return docs_a
            if source_type == "gdelt_article":
                return docs_b
            return []

        with (
            patch("intelligence.retriever.embed", return_value=_FAKE_VEC),
            patch("intelligence.retriever.search_similar", side_effect=_fake_search),
        ):
            from intelligence.retriever import retrieve_context
            result = retrieve_context("query", source_types=["x_tweet", "gdelt_article"])
        assert result.total_retrieved == 2


# ─────────────────────────────────────────────────────────────────────────────
# Seeder tests
# ─────────────────────────────────────────────────────────────────────────────


class TestSeeder:
    def test_iter_jsonl_parses_valid_lines(self, tmp_path):
        """_iter_jsonl yields dicts for valid JSON lines."""
        jfile = tmp_path / "test.jsonl"
        jfile.write_text('{"id":"1","text":"hello"}\n{"id":"2","text":"world"}\n')
        from intelligence.seeder import _iter_jsonl
        records = list(_iter_jsonl(jfile))
        assert len(records) == 2
        assert records[0]["id"] == "1"

    def test_iter_jsonl_skips_bad_lines(self, tmp_path):
        """_iter_jsonl skips malformed JSON without raising."""
        jfile = tmp_path / "test.jsonl"
        jfile.write_text('{"id":"1"}\nNOT_JSON\n{"id":"3"}\n')
        from intelligence.seeder import _iter_jsonl
        records = list(_iter_jsonl(jfile))
        assert len(records) == 2

    def test_extract_tickers_simple(self):
        """$TICKER dollar-sign pattern is extracted correctly."""
        from intelligence.seeder import _extract_tickers_simple
        tickers = _extract_tickers_simple("Bullish on $AAPL and $MSFT today!")
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_extract_tickers_caps_at_10(self):
        """_extract_tickers_simple returns at most 10 tickers."""
        from intelligence.seeder import _extract_tickers_simple
        text = " ".join(f"$TICK{i}" for i in range(20))
        tickers = _extract_tickers_simple(text)
        assert len(tickers) <= 10

    def test_parse_x_tweet_extracts_fields(self):
        """_parse_x_tweet populates all expected fields from a raw tweet dict."""
        from intelligence.seeder import _parse_x_tweet
        raw = {
            "id": "tweet_abc",
            "text": "Bullish on $AAPL today",
            "created_at": "2026-03-04T22:20:43.000Z",
            "author_username": "trader_joe",
            "author_followers": 1000,
            "engagement_score": 42,
            "engagement_normalized": 10.5,
            "metrics": {"like_count": 5},
        }
        result = _parse_x_tweet(raw, "harvest_test.jsonl")
        assert result is not None
        assert result["source_id"] == "tweet_abc"
        assert result["source_type"] == "x_tweet"
        assert "AAPL" in result["tickers"]
        assert result["metadata"]["author"] == "trader_joe"
        assert result["timestamp"] is not None

    def test_parse_x_tweet_skips_empty_text(self):
        """_parse_x_tweet returns None for records with empty text."""
        from intelligence.seeder import _parse_x_tweet
        result = _parse_x_tweet({"id": "1", "text": ""}, "file.jsonl")
        assert result is None

    def test_seed_x_tweets_missing_dir(self, tmp_path, caplog):
        """seed_x_tweets returns 0 and logs warning when archive dir missing."""
        import logging
        from intelligence.seeder import seed_x_tweets
        with caplog.at_level(logging.WARNING, logger="intelligence.seeder"):
            result = seed_x_tweets(tmp_path / "nonexistent")
        assert result == 0
        assert "not found" in caplog.text.lower() or "skipping" in caplog.text.lower()

    def test_seed_progress_logging(self, tmp_path, caplog):
        """Progress is logged every 500 records."""
        import logging

        # Create a JSONL file with 550 tweets
        jfile = tmp_path / "bulk.jsonl"
        lines = [json.dumps({"id": str(i), "text": f"tweet {i} about $AAPL"}) for i in range(550)]
        jfile.write_text("\n".join(lines))

        fake_embeddings = [[0.1] * 384] * 64  # fake batch output

        with (
            patch("intelligence.seeder.embed_batch", return_value=fake_embeddings),
            patch("intelligence.seeder.store_embeddings_batch", return_value=64),
            caplog.at_level(logging.INFO, logger="intelligence.seeder"),
        ):
            from intelligence.seeder import seed_x_tweets
            seed_x_tweets(tmp_path)

        progress_lines = [line for line in caplog.text.split("\n") if "progress" in line.lower()]
        assert len(progress_lines) >= 1

    def test_seed_calls_embed_and_store(self, tmp_path):
        """seed_x_tweets calls embed_batch and store_embeddings_batch."""
        jfile = tmp_path / "small.jsonl"
        jfile.write_text('{"id":"1","text":"hello $AAPL"}\n{"id":"2","text":"world $MSFT"}\n')

        with (
            patch("intelligence.seeder.embed_batch", return_value=[[0.1] * 384, [0.2] * 384]) as mock_embed,
            patch("intelligence.seeder.store_embeddings_batch", return_value=2) as mock_store,
        ):
            from intelligence.seeder import seed_x_tweets
            n = seed_x_tweets(tmp_path)

        mock_embed.assert_called_once()
        mock_store.assert_called_once()
        assert n == 2


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Contracts tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPydanticContracts:
    def test_embedding_record_valid(self):
        from cemini_contracts.vector import EmbeddingRecord
        rec = EmbeddingRecord(content="hello", source_type="x_tweet", tickers=["AAPL"])
        assert rec.content == "hello"
        assert rec.tickers == ["AAPL"]
        assert rec.source_id is None

    def test_similarity_result_valid(self):
        from cemini_contracts.vector import SimilarityResult
        r = SimilarityResult(id=1, content="text", source_type="x_tweet", similarity_score=0.85)
        assert r.similarity_score == 0.85

    def test_similarity_result_rejects_invalid_score(self):
        from pydantic import ValidationError
        from cemini_contracts.vector import SimilarityResult
        with pytest.raises(ValidationError):
            SimilarityResult(id=1, content="x", source_type="x_tweet", similarity_score=1.5)

    def test_similarity_with_market_result(self):
        from cemini_contracts.vector import MarketState, SimilarityWithMarketResult
        r = SimilarityWithMarketResult(
            id=2,
            content="intel",
            source_type="gdelt_article",
            similarity_score=0.75,
            market_state=MarketState(close=420.5, volume=1_000_000, rsi=55.0, ticker="SPY"),
        )
        assert r.market_state.ticker == "SPY"
        assert r.market_state.close == 420.5

    def test_graded_context_valid_grades(self):
        from cemini_contracts.vector import GradedContext
        for grade in ("RELEVANT", "AMBIGUOUS", "IRRELEVANT"):
            ctx = GradedContext(content="text", similarity_score=0.5, grade=grade, source_type="x_tweet")
            assert ctx.grade == grade

    def test_graded_context_rejects_invalid_grade(self):
        from pydantic import ValidationError
        from cemini_contracts.vector import GradedContext
        with pytest.raises(ValidationError):
            GradedContext(content="text", similarity_score=0.5, grade="UNKNOWN", source_type="x_tweet")

    def test_retrieval_result_defaults(self):
        from cemini_contracts.vector import RetrievalResult
        r = RetrievalResult()
        assert r.retrieval_quality == "insufficient"
        assert r.contexts == []
        assert r.total_relevant == 0

    def test_retrieval_result_quality_validation(self):
        from pydantic import ValidationError
        from cemini_contracts.vector import RetrievalResult
        with pytest.raises(ValidationError):
            RetrievalResult(retrieval_quality="excellent")

    def test_vector_store_stats_defaults(self):
        from cemini_contracts.vector import VectorStoreStats
        stats = VectorStoreStats()
        assert stats.total_embeddings == 0
        assert stats.by_source_type == {}
        assert stats.avg_per_day == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Realtime Worker tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRealtimeWorker:
    def test_handle_message_buffers_content(self):
        """_handle_message adds parsed message content to the buffer."""
        from intelligence.realtime_worker import EmbeddingWorker
        worker = EmbeddingWorker()
        msg = {
            "type": "pmessage",
            "channel": "intel:spy_trend",
            "data": json.dumps({"value": "bullish", "source_system": "regime_gate"}),
        }
        worker._handle_message(msg)
        assert len(worker._buffer) == 1
        assert worker._buffer[0]["content"] == "bullish"
        assert worker._buffer[0]["source_channel"] == "intel:spy_trend"
        assert worker._buffer[0]["source_type"] == "intel_message"

    def test_handle_message_skips_short_content(self):
        """Messages with very short content (< 5 chars) are ignored."""
        from intelligence.realtime_worker import EmbeddingWorker
        worker = EmbeddingWorker()
        msg = {
            "type": "pmessage",
            "channel": "intel:test",
            "data": json.dumps({"value": "ok"}),
        }
        worker._handle_message(msg)
        assert len(worker._buffer) == 0

    def test_handle_message_skips_bad_json(self):
        """Malformed JSON in message data does not crash the worker."""
        from intelligence.realtime_worker import EmbeddingWorker
        worker = EmbeddingWorker()
        msg = {"type": "pmessage", "channel": "intel:test", "data": "NOT_JSON"}
        # Should not raise
        worker._handle_message(msg)

    def test_stop_sets_running_false(self):
        """stop() sets _running to False."""
        from intelligence.realtime_worker import EmbeddingWorker
        worker = EmbeddingWorker()
        worker._running = True
        worker.stop()
        assert worker._running is False
