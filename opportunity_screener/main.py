"""
opportunity_screener/main.py — FastAPI App + Startup Lifecycle (Step 26.1g)

Endpoints:
  GET /health              — liveness + key metrics
  GET /metrics             — Prometheus scrape endpoint
  GET /watchlist           — current watchlist sorted by conviction
  GET /watchlist/history   — last 100 promotion/demotion events (Redis)
  GET /convictions         — all tracked tickers with conviction scores
  GET /convictions/{ticker}— single ticker conviction detail
  GET /stats               — processing stats

Usage (direct):
  python3 -m opportunity_screener.main
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from opportunity_screener.config import APP_HOST, APP_PORT
from opportunity_screener.screener import OpportunityScreener

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

    yield

    # Shutdown
    logger.info("OpportunityScreener shutdown")
    screening_task.cancel()
    decay_task.cancel()
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


if __name__ == "__main__":
    uvicorn.run(
        "opportunity_screener.main:app",
        host=APP_HOST,
        port=APP_PORT,
        log_level="info",
    )
