"""cemini_mcp — Redis intel bus readers.

All functions return dicts (not raw JSON strings).
Missing or unreadable keys return a graceful default with stale=True.
"""
import json
import logging
import time
from typing import Any, Optional

import redis as _redis_lib

try:
    import psycopg2
except ImportError:
    psycopg2 = None  # type: ignore

from cemini_mcp.config import (
    REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, STALE_THRESHOLD_SEC,
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
)

logger = logging.getLogger("cemini_mcp.readers")

# Keys that are NOT wrapped in IntelPayload (raw values or flat dicts)
_RAW_KEYS = {"strategy_mode", "intel:btc_spy_corr"}
# GDELT keys store flat dicts / arrays with no IntelPayload envelope
_GDELT_KEYS = {"intel:geopolitical_risk", "intel:regional_risk", "intel:conflict_events"}


def _client() -> _redis_lib.Redis:
    return _redis_lib.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
        decode_responses=True, socket_connect_timeout=2,
    )


def _staleness(timestamp: float) -> dict:
    age = time.time() - timestamp
    return {"stale": age > STALE_THRESHOLD_SEC, "age_seconds": round(age, 1)}


def _missing(key: str) -> dict:
    return {"stale": True, "age_seconds": None, "error": f"key_missing:{key}"}


def read_intel(key: str) -> dict:
    """Read an IntelPayload-wrapped key. Returns the full envelope as a dict."""
    try:
        r = _client()
        raw = r.get(key)
        r.close()
    except Exception as exc:
        logger.debug("Redis GET failed (%s): %s", key, exc)
        return _missing(key)

    if not raw:
        return _missing(key)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _missing(key)

    if isinstance(payload, dict) and "timestamp" in payload:
        payload.update(_staleness(payload["timestamp"]))

    return payload


def read_raw(key: str) -> Optional[str]:
    """Read a plain string key (strategy_mode, btc_spy_corr)."""
    try:
        r = _client()
        val = r.get(key)
        r.close()
        return val
    except Exception as exc:
        logger.debug("Redis GET raw failed (%s): %s", key, exc)
        return None


def read_json(key: str) -> Any:
    """Read a key whose value is a JSON blob (GDELT keys, list payloads)."""
    try:
        r = _client()
        raw = r.get(key)
        r.close()
    except Exception as exc:
        logger.debug("Redis GET json failed (%s): %s", key, exc)
        return None

    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def read_ttl(key: str) -> int:
    """Return TTL in seconds (-1 = no expiry, -2 = missing)."""
    try:
        r = _client()
        ttl = r.ttl(key)
        r.close()
        return ttl
    except Exception:
        return -2


def read_risk_from_postgres() -> dict:
    """Read the latest risk snapshot from playbook_logs (Postgres).

    Risk is NOT published to Redis — it only lives in Postgres + JSONL.
    Returns a dict with cvar_99, kelly_size, nav, drawdown_snapshot, timestamp.
    """
    if psycopg2 is None:
        return {"error": "psycopg2_not_available", "stale": True}

    sql = """
        SELECT payload, EXTRACT(EPOCH FROM timestamp) AS ts
        FROM playbook_logs
        WHERE log_type = 'risk'
        ORDER BY timestamp DESC
        LIMIT 1
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME,
            connect_timeout=3,
        )
        cur = conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return {"error": "no_risk_data", "stale": True}

        payload, ts = row
        if isinstance(payload, str):
            payload = json.loads(payload)
        payload["timestamp"] = float(ts)
        payload.update(_staleness(float(ts)))
        return payload

    except Exception as exc:
        logger.debug("Postgres risk read failed: %s", exc)
        return {"error": str(exc)[:120], "stale": True}


def health_check_all() -> dict:
    """Return a health report dict for every intel key + Postgres."""
    intel_keys = [
        "intel:playbook_snapshot",
        "intel:spy_trend",
        "intel:vix_level",
        "intel:fed_bias",
        "intel:btc_sentiment",
        "intel:portfolio_heat",
        "intel:btc_spy_corr",
        "strategy_mode",
        "intel:kalshi_orderbook_summary",
        "intel:geopolitical_risk",
        "intel:regional_risk",
        "intel:conflict_events",
        "intel:btc_spy_corr",
        "intel:social_score",
        "intel:weather_edge",
        "intel:kalshi_oi",
        "intel:kalshi_liquidity_spike",
    ]

    sources: dict[str, Any] = {}
    try:
        r = _client()
        for key in intel_keys:
            raw = r.get(key)
            ttl = r.ttl(key)
            if raw is None:
                sources[key] = {"status": "missing", "ttl": ttl}
                continue
            try:
                parsed = json.loads(raw)
                ts = parsed.get("timestamp") if isinstance(parsed, dict) else None
                if ts:
                    age = round(time.time() - ts, 1)
                    status = "stale" if age > STALE_THRESHOLD_SEC else "ok"
                    sources[key] = {"status": status, "age_seconds": age, "ttl": ttl}
                else:
                    sources[key] = {"status": "ok_no_ts", "ttl": ttl}
            except json.JSONDecodeError:
                sources[key] = {"status": "ok_raw", "ttl": ttl}
        r.close()
        redis_status = "ok"
    except Exception as exc:
        redis_status = f"error:{exc!s:.80}"

    # Postgres check
    try:
        if psycopg2 is None:
            raise ImportError("psycopg2 not available")
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME,
            connect_timeout=3,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM playbook_logs WHERE log_type='risk'")
        risk_count = cur.fetchone()[0]
        cur.close()
        conn.close()
        pg_status = "ok"
        pg_risk_rows = risk_count
    except Exception as exc:
        pg_status = f"error:{exc!s:.80}"
        pg_risk_rows = None

    healthy = sum(1 for v in sources.values() if v.get("status") in ("ok", "ok_raw", "ok_no_ts"))
    total = len(sources)

    return {
        "redis": redis_status,
        "postgres": pg_status,
        "postgres_risk_rows": pg_risk_rows,
        "sources": sources,
        "healthy_count": healthy,
        "total_count": total,
        "timestamp": time.time(),
    }
