"""cemini_mcp — FastMCP Intelligence Server.

Exposes the Cemini intel:* Redis bus as typed, callable MCP tools.
All tools are read-only (destructive=False).

Transport: streamable-http on MCP_PORT (default 8002).
"""
import logging
import time
from typing import Any, Optional

from fastmcp import FastMCP

from cemini_mcp import readers
from cemini_mcp.config import MCP_HOST, MCP_PORT

logger = logging.getLogger("cemini_mcp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

mcp = FastMCP(
    name="Cemini Intelligence Server",
    instructions=(
        "Read-only intelligence tools for the Cemini Financial Suite. "
        "Query macro regime, signal detections, risk metrics, Kalshi markets, "
        "geopolitical risk, and cross-asset sentiment. "
        "All tools are safe to call concurrently. "
        "Stale data is flagged with stale=true in the response."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# 1. Regime Status
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_regime_status() -> dict[str, Any]:
    """Current macro regime (GREEN/YELLOW/RED).

    Includes SPY vs EMA21/SMA50 comparison, JNK/TLT cross-validation flag,
    confidence level, and the human-readable reason string.

    Source: intel:playbook_snapshot (PlaybookLogger, every 5 minutes).
    """
    envelope = readers.read_intel("intel:playbook_snapshot")
    if envelope.get("error"):
        return {"regime": "UNKNOWN", "detail": {}, **envelope}

    value = envelope.get("value", {})
    if isinstance(value, dict) and "detail" in value:
        # regime variant: {"regime": "RED", "detail": {RegimeSnapshot fields}}
        return {
            "regime": value.get("regime", "UNKNOWN"),
            "detail": value.get("detail", {}),
            "source": envelope.get("source_system", "playbook_logger"),
            "confidence": envelope.get("confidence", 0.0),
            "stale": envelope.get("stale", False),
            "age_seconds": envelope.get("age_seconds"),
        }

    # Signal variant or old format — return what we have
    return {
        "regime": "UNKNOWN",
        "detail": value if isinstance(value, dict) else {},
        "note": "snapshot contains latest_signal not regime",
        "stale": envelope.get("stale", False),
        "age_seconds": envelope.get("age_seconds"),
    }


# ---------------------------------------------------------------------------
# 2. Signal Detections
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_signal_detections(
    ticker: Optional[str] = None,
) -> dict[str, Any]:
    """Latest detected signal from the 6-pattern signal catalog.

    Detectors: EpisodicPivot, MomentumBurst, ElephantBar, VCP,
    HighTightFlag, InsideBar212.

    Note: Redis stores the single most-recent signal. For historical
    data, query Postgres playbook_logs WHERE log_type='signal'.

    Args:
        ticker: Filter by symbol (case-insensitive). Omit for any ticker.

    Source: intel:playbook_snapshot (PlaybookLogger).
    """
    envelope = readers.read_intel("intel:playbook_snapshot")
    if envelope.get("error"):
        return {"signal": None, "note": "no_data", **envelope}

    value = envelope.get("value", {})
    signal = None

    if isinstance(value, dict):
        if "latest_signal" in value:
            signal = value["latest_signal"]
        elif "detail" in value:
            # regime variant — no signal available
            return {
                "signal": None,
                "note": "snapshot_contains_regime_not_signal",
                "regime": value.get("regime"),
                "stale": envelope.get("stale", False),
                "age_seconds": envelope.get("age_seconds"),
            }

    if signal and ticker:
        if signal.get("symbol", "").upper() != ticker.upper():
            signal = None

    return {
        "signal": signal,
        "stale": envelope.get("stale", False),
        "age_seconds": envelope.get("age_seconds"),
        "source": envelope.get("source_system", "playbook_logger"),
    }


# ---------------------------------------------------------------------------
# 3. Risk Metrics
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_risk_metrics() -> dict[str, Any]:
    """Current risk engine snapshot: CVaR (99th percentile), fractional
    Kelly size, net asset value, and drawdown monitor state.

    Risk data is persisted to Postgres (not Redis). This tool queries
    playbook_logs WHERE log_type='risk' for the most recent row.

    Source: Postgres playbook_logs (PlaybookLogger.log_risk_snapshot).
    """
    return readers.read_risk_from_postgres()


# ---------------------------------------------------------------------------
# 4. Full Playbook Snapshot
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_playbook_snapshot() -> dict[str, Any]:
    """Raw intel:playbook_snapshot envelope — the latest playbook output.

    Contains either a regime snapshot or a signal detection, depending
    on what the playbook runner logged most recently. Updated every
    5 minutes by the PlaybookLogger.

    For structured regime data use get_regime_status().
    For structured signal data use get_signal_detections().
    For risk data use get_risk_metrics().

    Source: intel:playbook_snapshot (PlaybookLogger).
    """
    return readers.read_intel("intel:playbook_snapshot")


# ---------------------------------------------------------------------------
# 5. Kalshi Intel
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_kalshi_intel(category: Optional[str] = None) -> dict[str, Any]:
    """Rover scanner intelligence — live Kalshi market summary.

    Returns active market counts, category breakdown, and orderbook
    tickers from the WebSocket rover (ws_rover.py). Updated every 5 min.

    Args:
        category: Filter summary by category (e.g. 'weather', 'crypto',
                  'politics'). Omit for full summary.

    Source: intel:kalshi_orderbook_summary (WebSocketRover).
    """
    envelope = readers.read_intel("intel:kalshi_orderbook_summary")
    if envelope.get("error"):
        return {"summary": None, **envelope}

    value = envelope.get("value", {})

    if category and isinstance(value, dict):
        breakdown = value.get("category_breakdown", {})
        return {
            "category": category,
            "count": breakdown.get(category, 0),
            "full_breakdown": breakdown,
            "active_markets": value.get("active_markets"),
            "stale": envelope.get("stale", False),
            "age_seconds": envelope.get("age_seconds"),
        }

    return {
        "summary": value,
        "stale": envelope.get("stale", False),
        "age_seconds": envelope.get("age_seconds"),
        "source": envelope.get("source_system"),
    }


# ---------------------------------------------------------------------------
# 6. Geopolitical Risk
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_geopolitical_risk() -> dict[str, Any]:
    """GDELT-derived geopolitical risk score and top conflict events.

    Scores range 0–100. Level: LOW / MODERATE / ELEVATED / HIGH / CRITICAL.
    Trend: STABLE / RISING / FALLING.
    Updated every 15 minutes by the GDELT harvester.

    Returns risk score, level, trend, top event, regional breakdown,
    and the first 5 high-impact conflict events.

    Source: intel:geopolitical_risk + intel:regional_risk + intel:conflict_events.
    """
    geo_risk = readers.read_json("intel:geopolitical_risk") or {}
    regional = readers.read_json("intel:regional_risk") or {}
    events_raw = readers.read_json("intel:conflict_events") or []

    top_events = events_raw[:5] if isinstance(events_raw, list) else []

    return {
        "risk_score": geo_risk.get("score"),
        "level": geo_risk.get("level"),
        "trend": geo_risk.get("trend"),
        "top_event": geo_risk.get("top_event"),
        "num_high_impact_events": geo_risk.get("num_high_impact_events"),
        "updated_at": geo_risk.get("updated_at"),
        "regional_risk": regional,
        "top_conflict_events": top_events,
        "stale": not bool(geo_risk),
    }


# ---------------------------------------------------------------------------
# 7. Sentiment Aggregation
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_sentiment(source: Optional[str] = None) -> dict[str, Any]:
    """Cross-asset sentiment aggregated from all intel bus sources.

    Available sources:
      btc_sentiment  — float -1 to 1 (SatoshiAnalyzer)
      fed_bias       — dict {bias: dovish/hawkish/neutral, confidence}
      spy_trend      — bullish / bearish / neutral (analyzer.py)
      vix_level      — float VIX proxy (analyzer.py)
      portfolio_heat — float 0-1 exposure level (analyzer.py)
      btc_spy_corr   — float BTC/SPY 30-day correlation

    Args:
        source: Return only this source. Omit for all sources.

    Source: Multiple intel:* keys.
    """
    def _extract_value(envelope: dict):
        if envelope.get("error"):
            return {"value": None, "stale": True}
        return {
            "value": envelope.get("value"),
            "stale": envelope.get("stale", False),
            "age_seconds": envelope.get("age_seconds"),
            "confidence": envelope.get("confidence"),
        }

    all_sources = {
        "btc_sentiment": lambda: _extract_value(readers.read_intel("intel:btc_sentiment")),
        "fed_bias": lambda: _extract_value(readers.read_intel("intel:fed_bias")),
        "spy_trend": lambda: _extract_value(readers.read_intel("intel:spy_trend")),
        "vix_level": lambda: _extract_value(readers.read_intel("intel:vix_level")),
        "portfolio_heat": lambda: _extract_value(readers.read_intel("intel:portfolio_heat")),
        "btc_spy_corr": lambda: {
            "value": _parse_float(readers.read_raw("intel:btc_spy_corr")),
            "stale": False,
        },
    }

    if source:
        if source not in all_sources:
            return {"error": f"unknown_source:{source}", "available": list(all_sources)}
        return {source: all_sources[source]()}

    return {k: fn() for k, fn in all_sources.items()}


def _parse_float(val: Optional[str]) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 8. Strategy Mode
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_strategy_mode() -> dict[str, Any]:
    """Current strategy mode set by the coach analyzer.

    Modes: conservative | aggressive | sniper
      conservative — low confidence, wide spreads
      aggressive   — strong trend, FGI 40-60
      sniper       — extreme fear/greed, contrarian positioning

    Also returns correlated intel (VIX proxy, SPY trend, portfolio heat)
    to explain the mode selection.

    Source: strategy_mode key (analyzer.py) + correlated intel:* keys.
    """
    mode = readers.read_raw("strategy_mode") or "unknown"
    vix_env = readers.read_intel("intel:vix_level")
    spy_env = readers.read_intel("intel:spy_trend")
    heat_env = readers.read_intel("intel:portfolio_heat")

    return {
        "mode": mode,
        "supporting_signals": {
            "vix_level": vix_env.get("value"),
            "spy_trend": spy_env.get("value"),
            "portfolio_heat": heat_env.get("value"),
        },
        "signal_ages": {
            "vix_level": vix_env.get("age_seconds"),
            "spy_trend": spy_env.get("age_seconds"),
            "portfolio_heat": heat_env.get("age_seconds"),
        },
        "stale": any(
            e.get("stale", True)
            for e in (vix_env, spy_env, heat_env)
            if not e.get("error")
        ),
    }


# ---------------------------------------------------------------------------
# 9. Data Health
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_data_health() -> dict[str, Any]:
    """Pipeline health dashboard — data freshness per source.

    Reports status for every intel:* Redis key and Postgres connectivity.
    A buyer's first call to verify the system is alive.

    Status values per source:
      ok         — data present and fresh
      stale      — data present but older than STALE_THRESHOLD_SEC
      missing    — key does not exist in Redis
      ok_raw     — key exists but no timestamp (raw value)
      ok_no_ts   — JSON key exists but no timestamp field

    Source: Redis KEYS + TTL scan + Postgres connectivity check.
    """
    return readers.health_check_all()


# ---------------------------------------------------------------------------
# 10. Contract Pricing (Logit Jump-Diffusion)
# ---------------------------------------------------------------------------
@mcp.tool(annotations={"destructive": False, "readOnly": True})
def get_contract_pricing(ticker: Optional[str] = None) -> dict[str, Any]:
    """Logit-space contract pricing assessments for Kalshi markets.

    Uses the Shaw & Dalen Logit Jump-Diffusion model to compute
    mispricing scores, regime classification (diffusion vs jump),
    confidence, and fair-value probabilities for each actively-tracked
    Kalshi market.

    Markets in 'jump' regime are flagged human_review=True — these
    should be manually reviewed before auto-trading.

    Args:
        ticker: Return assessment for a single ticker. Omit for all.

    Source: intel:logit_assessments (WebSocketRover, every 5 min).
    """
    envelope = readers.read_intel("intel:logit_assessments")
    if envelope.get("error"):
        return {"assessments": None, **envelope}

    value = envelope.get("value", {})
    if not isinstance(value, dict) or not value:
        return {
            "assessments": None,
            "note": "no_assessments_yet — rover needs 10+ orderbook observations per ticker",
            "stale": envelope.get("stale", True),
        }

    if ticker:
        assessment = value.get(ticker)
        return {
            "ticker": ticker,
            "assessment": assessment,
            "found": assessment is not None,
            "total_assessed": len(value),
            "stale": envelope.get("stale", False),
            "age_seconds": envelope.get("age_seconds"),
        }

    jump_markets = [t for t, a in value.items() if isinstance(a, dict) and a.get("human_review")]
    return {
        "total_assessed": len(value),
        "jump_regime_markets": jump_markets,
        "assessments": value,
        "stale": envelope.get("stale", False),
        "age_seconds": envelope.get("age_seconds"),
        "source": envelope.get("source_system"),
    }


# ---------------------------------------------------------------------------
# Prometheus /metrics endpoint (Step 35a)
# Uses prometheus_client to expose process + custom metrics via custom_route.
# ---------------------------------------------------------------------------
try:
    import prometheus_client
    from starlette.requests import Request
    from starlette.responses import Response as StarletteResponse

    @mcp.custom_route("/metrics", methods=["GET"])
    async def prometheus_metrics(request: Request) -> StarletteResponse:
        """Expose Prometheus metrics for scraping."""
        data = prometheus_client.generate_latest()
        return StarletteResponse(
            content=data,
            media_type=prometheus_client.CONTENT_TYPE_LATEST,
        )
except ImportError:
    logger.warning("prometheus_client not installed — /metrics endpoint unavailable")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    logger.info("Starting Cemini MCP Intelligence Server on %s:%d", MCP_HOST, MCP_PORT)
    asyncio.run(
        mcp.run_http_async(
            host=MCP_HOST,
            port=MCP_PORT,
            transport="streamable-http",
        )
    )
