"""
Polars-native data loading from Postgres.
Falls back to psycopg2 if connectorx is not available.
"""
from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Optional

import polars as pl

logger = logging.getLogger("cemini.feature_engine.data_loader")


def get_db_uri() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "admin")
    password = os.getenv("POSTGRES_PASSWORD", "quest")
    db = os.getenv("POSTGRES_DB", "qdb")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _read_via_psycopg2(query: str, schema: dict) -> pl.DataFrame:
    """Fallback loader using psycopg2 when connectorx is unavailable."""
    import psycopg2  # noqa: PLC0415

    uri = get_db_uri()
    conn = psycopg2.connect(uri)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return pl.DataFrame(schema=schema)
        col_names = [desc[0] for desc in cursor.description]
        data = {col: [row[i] for row in rows] for i, col in enumerate(col_names)}
        return pl.DataFrame(data).cast(schema)
    finally:
        conn.close()


def _read_query(query: str, schema: Optional[dict] = None) -> pl.DataFrame:
    """Read a SQL query into a Polars DataFrame."""
    uri = get_db_uri()
    try:
        df = pl.read_database_uri(query, uri, engine="connectorx")
        return df
    except Exception:
        logger.debug("connectorx unavailable, falling back to psycopg2")
    try:
        df = pl.read_database_uri(query, uri, engine="adbc")
        return df
    except Exception:
        logger.debug("adbc unavailable, falling back to psycopg2")
    if schema is not None:
        return _read_via_psycopg2(query, schema)
    return _read_via_psycopg2(query, {})


def load_market_ticks(ticker: str, start: str, end: str) -> pl.DataFrame:
    """Load 1-min OHLCV for a single ticker."""
    query = (
        "SELECT timestamp, open, high, low, close, volume "
        "FROM raw_market_ticks "
        f"WHERE symbol = '{ticker}' "  # noqa: S608
        f"AND timestamp >= '{start}' AND timestamp < '{end}' "
        "ORDER BY timestamp"
    )
    return _read_query(query)


def load_macro_logs(start: str, end: str) -> pl.DataFrame:
    """Load macro_logs (FGI, yields) for alignment."""
    query = (
        "SELECT timestamp, fear_greed_index, treasury_yield "
        "FROM macro_logs "
        f"WHERE timestamp >= '{start}' AND timestamp < '{end}' "  # noqa: S608
        "ORDER BY timestamp"
    )
    return _read_query(query)


def load_playbook_regime(start: str, end: str) -> pl.DataFrame:
    """Load regime state from playbook_logs."""
    query = (
        "SELECT timestamp, regime "
        "FROM playbook_logs "
        f"WHERE timestamp >= '{start}' AND timestamp < '{end}' "  # noqa: S608
        "ORDER BY timestamp"
    )
    return _read_query(query)


def _psycopg2_fetch(query: str, params: tuple = ()) -> tuple[list, list]:
    """Execute a parameterized query via psycopg2; returns (rows, col_names)."""
    import psycopg2  # noqa: PLC0415

    conn = psycopg2.connect(get_db_uri())
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        return rows, cols
    finally:
        conn.close()


def load_vol_surface(ticker: str, start: str, end: str) -> pl.DataFrame:
    """Load per-symbol vol surface snapshots for join_asof backward alignment.

    Extracts ticker-specific realized_vol_21d, vol_regime, and beta_to_spy
    from the JSONB payload of vol_surface_log.  Returns an empty DataFrame
    (with correct schema) if no rows exist or on any DB error.
    """
    _schema = {
        "timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
        "realized_vol_21d": pl.Float64,
        "vol_regime_str": pl.Utf8,
        "beta_to_spy": pl.Float64,
    }
    query = """
        SELECT
            timestamp,
            (payload->'symbols'->%s->>'realized_vol_21d')::float AS realized_vol_21d,
            payload->'symbols'->%s->>'vol_regime' AS vol_regime_str,
            (payload->'symbols'->%s->>'beta_to_spy')::float AS beta_to_spy
        FROM vol_surface_log
        WHERE timestamp >= %s AND timestamp < %s
          AND payload->'symbols' ? %s
        ORDER BY timestamp
    """
    try:
        rows, cols = _psycopg2_fetch(query, (ticker, ticker, ticker, start, end, ticker))
        if not rows:
            return pl.DataFrame(schema=_schema)
        data: dict = {col: [row[i] for row in rows] for i, col in enumerate(cols)}
        return pl.DataFrame(data).with_columns(
            pl.col("realized_vol_21d").cast(pl.Float64),
            pl.col("beta_to_spy").cast(pl.Float64),
        )
    except Exception as exc:
        logger.debug("load_vol_surface failed for %s: %s", ticker, exc)
        return pl.DataFrame(schema=_schema)


def load_sector_rotation(start: str, end: str) -> pl.DataFrame:
    """Load sector rotation snapshots for join_asof backward alignment.

    Returns timestamp + rotation_bias (RISK_ON/RISK_OFF/NEUTRAL).
    Returns empty DataFrame if no rows exist or on any DB error.
    """
    _schema = {
        "timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
        "rotation_bias": pl.Utf8,
    }
    query = """
        SELECT timestamp, rotation_bias
        FROM sector_rotation_log
        WHERE timestamp >= %s AND timestamp < %s
        ORDER BY timestamp
    """
    try:
        rows, cols = _psycopg2_fetch(query, (start, end))
        if not rows:
            return pl.DataFrame(schema=_schema)
        data = {col: [row[i] for row in rows] for i, col in enumerate(cols)}
        return pl.DataFrame(data)
    except Exception as exc:
        logger.debug("load_sector_rotation failed: %s", exc)
        return pl.DataFrame(schema=_schema)


def load_earnings_proximity(ticker: str, reference_date: str) -> tuple[float, int]:
    """Compute (earnings_proximity, earnings_cluster) for a ticker.

    earnings_proximity = 1.0 / (days_until_earnings + 1), 0.0 if CLEAR/no data.
    earnings_cluster   = 1 if 3+ distinct symbols report within ±7 days of this
                         ticker's next earnings date, else 0.

    Args:
        ticker:         Equity symbol, e.g. "AAPL".
        reference_date: ISO date string (YYYY-MM-DD or datetime prefix) used as
                        "today" for computing days_until.

    Returns:
        (earnings_proximity, earnings_cluster)
    """
    try:
        ref = date.fromisoformat(reference_date[:10])
    except ValueError:
        return 0.0, 0

    # Nearest upcoming (or today's) earnings for this ticker
    query_next = """
        SELECT estimated_date
        FROM earnings_calendar
        WHERE symbol = %s
          AND status != 'CLEAR'
          AND estimated_date >= %s
        ORDER BY estimated_date
        LIMIT 1
    """
    try:
        rows, _ = _psycopg2_fetch(query_next, (ticker, ref.isoformat()))
    except Exception as exc:
        logger.debug("load_earnings_proximity DB error for %s: %s", ticker, exc)
        return 0.0, 0

    if not rows or rows[0][0] is None:
        return 0.0, 0

    estimated = rows[0][0]  # datetime.date from psycopg2
    if isinstance(estimated, str):
        estimated = date.fromisoformat(estimated)

    days_until = max(0, (estimated - ref).days)
    proximity = 1.0 / (days_until + 1)

    # Earnings cluster: count symbols reporting within ±7 days of estimated
    cluster_start = estimated - timedelta(days=7)
    cluster_end = estimated + timedelta(days=7)
    query_cluster = """
        SELECT COUNT(DISTINCT symbol)
        FROM earnings_calendar
        WHERE estimated_date >= %s
          AND estimated_date <= %s
          AND status != 'CLEAR'
    """
    try:
        rows2, _ = _psycopg2_fetch(query_cluster, (cluster_start.isoformat(), cluster_end.isoformat()))
        cluster_count = int(rows2[0][0]) if rows2 and rows2[0][0] is not None else 0
    except Exception:
        cluster_count = 0

    return proximity, int(cluster_count >= 3)


def load_fred_data(series_id: str, start: str, end: str) -> pl.DataFrame:
    """Load FRED macro series."""
    query = (
        "SELECT observation_date AS timestamp, value "
        "FROM fred_observations "
        f"WHERE series_id = '{series_id}' "  # noqa: S608
        f"AND observation_date >= '{start}' AND observation_date < '{end}' "
        "ORDER BY observation_date"
    )
    return _read_query(query)
