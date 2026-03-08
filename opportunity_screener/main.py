"""
opportunity_screener/main.py — FastAPI App + Startup Lifecycle (Step 26.1g + Step 29)

Endpoints:
  GET /health              — liveness + key metrics
  GET /metrics             — Prometheus scrape endpoint
  GET /watchlist           — current watchlist sorted by conviction
  GET /watchlist/history   — last 100 promotion/demotion events (Redis)
  GET /convictions         — all tracked tickers with conviction scores
  GET /convictions/{ticker}— single ticker conviction detail
  GET /stats               — processing stats

  Step 29 — Vector Intelligence:
  GET  /vectors/stats                          — embedding count, breakdown by source
  POST /vectors/search                         — semantic similarity search
  POST /vectors/search_with_market             — similarity search + market state JOIN
  GET  /vectors/similar/{source_type}/{source_id} — docs similar to a stored doc
  POST /vectors/embed                          — manually embed and store text

Usage (direct):
  python3 -m opportunity_screener.main
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from opportunity_screener.config import APP_HOST, APP_PORT
from opportunity_screener.screener import OpportunityScreener

# ── Vector intelligence (Step 29) — graceful import ───────────────────────────
try:
    from intelligence import vector_store as _vs
    from intelligence.embedder import embed as _embed
    from intelligence.realtime_worker import EmbeddingWorker
    _VECTOR_AVAILABLE = True
except ImportError:
    _VECTOR_AVAILABLE = False
    _vs = None  # type: ignore[assignment]
    _embed = None  # type: ignore[assignment]
    EmbeddingWorker = None  # type: ignore[assignment]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("screener.app")

# ── Global screener instance ──────────────────────────────────────────────────
_screener = OpportunityScreener()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown lifecycle."""
    logger.info("OpportunityScreener startup")
    _screener.startup()

    # Launch background tasks
    screening_task = asyncio.create_task(_screener.run_screening_loop())
    decay_task = asyncio.create_task(_screener.run_decay_loop())

    # Step 29 — Real-time embedding pipeline (optional; skipped if intelligence not installed)
    embedding_task = None
    _embedding_worker = None
    if _VECTOR_AVAILABLE and EmbeddingWorker is not None:
        _embedding_worker = EmbeddingWorker()
        embedding_task = asyncio.create_task(_embedding_worker.run())
        logger.info("EmbeddingWorker started (real-time intel:* embedding)")
    else:
        logger.info("intelligence module not available — EmbeddingWorker skipped")

    yield

    # Shutdown
    logger.info("OpportunityScreener shutdown")
    screening_task.cancel()
    decay_task.cancel()
    if embedding_task is not None and _embedding_worker is not None:
        _embedding_worker.stop()
        embedding_task.cancel()
    _screener.shutdown()


app = FastAPI(
    title="Opportunity Discovery Engine",
    description=(
        "Step 26.1 — Intelligence-in, ticker-out. "
        "Bayesian conviction scoring over intel:* channels. "
        "Exposes dynamic 50-ticker watchlist for downstream signal machinery."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Prometheus metrics (Step 35 pattern)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    pass

# OpenTelemetry tracing (Step 35d pattern)
try:
    import sys
    sys.path.insert(0, "/app")
    from observability.tracing import configure_tracing, instrument_fastapi
    configure_tracing("opportunity_screener")
    instrument_fastapi(app)
except Exception:
    pass


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, Any]:
    """Liveness probe + key operational metrics."""
    stats = _screener.get_stats()
    return {
        "status": "healthy",
        "watchlist_size": stats["watchlist_size"],
        "tickers_tracked": stats["tickers_tracked"],
        "messages_processed": stats["messages_processed"],
        "uptime_seconds": stats["uptime_seconds"],
    }


@app.get("/watchlist")
async def get_watchlist() -> dict[str, Any]:
    """Current watchlist sorted by conviction descending."""
    return {
        "watchlist": _screener._watchlist.get_watchlist(),
        "dynamic_count": _screener._watchlist.dynamic_count(),
        "core_tickers": list(_screener._watchlist._core),
        "total_slots_used": _screener._watchlist.get_size(),
        "timestamp": time.time(),
    }


@app.get("/watchlist/history")
async def get_watchlist_history() -> dict[str, Any]:
    """Last 100 promotion/demotion events from Redis (intel:watchlist_update)."""
    r = _screener._redis
    if r is None:
        return {"events": [], "note": "Redis not connected"}
    try:
        # Read current update (single-key model — future: use Redis Stream)
        raw = r.get("intel:watchlist_update")
        if raw:
            import json
            event = json.loads(raw)
            return {"events": [event.get("value", event)], "note": "last event only (Redis Stream in Phase 2)"}
        return {"events": []}
    except Exception as exc:
        return {"events": [], "error": str(exc)}


@app.get("/convictions")
async def get_convictions() -> dict[str, Any]:
    """All tracked tickers with conviction scores."""
    tickers = _screener._conviction.all_tickers()
    result = []
    for t in sorted(tickers, key=lambda x: _screener._conviction.get_conviction(x), reverse=True):
        state = _screener._conviction.get_state(t) or {}
        result.append({
            "ticker": t,
            "conviction": state.get("conviction", 0.5),
            "last_updated": state.get("last_updated", ""),
            "source_count": state.get("source_count", 0),
            "sources": state.get("sources", []),
            "first_seen": state.get("first_seen", ""),
        })
    return {"convictions": result, "total": len(result)}


@app.get("/convictions/{ticker}")
async def get_conviction(ticker: str) -> dict[str, Any]:
    """Single ticker conviction detail."""
    ticker = ticker.upper()
    state = _screener._conviction.get_state(ticker)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not tracked")
    return {
        "ticker": ticker,
        "conviction": state.get("conviction", 0.5),
        "last_updated": state.get("last_updated", ""),
        "source_count": state.get("source_count", 0),
        "sources": state.get("sources", []),
        "first_seen": state.get("first_seen", ""),
        "on_watchlist": _screener._watchlist.is_watched(ticker),
    }


@app.get("/stats")
async def get_stats() -> dict[str, Any]:
    """Processing statistics."""
    return _screener.get_stats()


# ── Step 29: Vector Intelligence Endpoints ────────────────────────────────────

def _require_vectors():
    if not _VECTOR_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Vector intelligence module not available. Install sentence-transformers + pgvector.",
        )


@app.get("/vectors/stats")
def get_vector_stats() -> dict[str, Any]:
    """Embedding count, breakdown by source type, oldest/newest timestamps."""
    _require_vectors()
    try:
        return _vs.get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vectors/search")
def vector_search(body: dict[str, Any]) -> dict[str, Any]:
    """Semantic similarity search.

    Body: {query: str, limit?: int, source_type?: str, tickers?: list[str], since?: str}
    Returns: {results: list[SimilarityResult], count: int}
    """
    _require_vectors()
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="'query' is required")

    limit = int(body.get("limit", 10))
    source_type = body.get("source_type")
    tickers = body.get("tickers") or None
    since_str = body.get("since")
    since = None
    if since_str:
        from datetime import datetime
        try:
            since = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid 'since' format: {exc}") from exc

    try:
        query_vec = _embed(query)
        results = _vs.search_similar(
            query_vec,
            limit=limit,
            source_type=source_type,
            tickers=tickers,
            since=since,
        )
        return {"results": results, "count": len(results), "query": query}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vectors/search_with_market")
def vector_search_with_market(body: dict[str, Any]) -> dict[str, Any]:
    """Semantic search + TimescaleDB market state JOIN.

    Body: {query: str, limit?: int, tickers?: list[str]}
    Returns: {results: list[SimilarityWithMarketResult], count: int}
    """
    _require_vectors()
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="'query' is required")

    limit = int(body.get("limit", 10))
    tickers = body.get("tickers") or None

    try:
        query_vec = _embed(query)
        results = _vs.search_similar_with_market_context(query_vec, limit=limit, tickers=tickers)
        return {"results": results, "count": len(results), "query": query}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/vectors/similar/{source_type}/{source_id}")
def get_similar(source_type: str, source_id: str, limit: int = 10) -> dict[str, Any]:
    """Find documents similar to a specific stored document."""
    _require_vectors()
    try:
        doc = _vs.get_embedding_by_source(source_type, source_id)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Document {source_type}/{source_id} not found")
        results = _vs.search_similar(doc["embedding"], limit=limit + 1)
        # Exclude the source document itself
        results = [r for r in results if r["id"] != doc["id"]][:limit]
        return {"results": results, "count": len(results), "source": {"source_type": source_type, "source_id": source_id}}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vectors/embed")
def manual_embed(body: dict[str, Any]) -> dict[str, Any]:
    """Manually embed and store a text string (for testing/one-offs).

    Body: {content: str, source_type?: str, source_id?: str, metadata?: dict, tickers?: list}
    Returns: {id: int, embedding_dim: int}
    """
    _require_vectors()
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="'content' is required")

    source_type = body.get("source_type", "manual")
    source_id = body.get("source_id")
    metadata = body.get("metadata") or {}
    tickers = body.get("tickers") or []

    try:
        embedding = _embed(content)
        row_id = _vs.store_embedding(
            content=content,
            embedding=embedding,
            source_type=source_type,
            source_id=source_id,
            metadata=metadata,
            tickers=tickers,
        )
        return {"id": row_id, "embedding_dim": len(embedding), "source_type": source_type}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    uvicorn.run(
        "opportunity_screener.main:app",
        host=APP_HOST,
        port=APP_PORT,
        log_level="info",
    )
