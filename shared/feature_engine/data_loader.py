"""
Polars-native data loading from Postgres.
Falls back to psycopg2 if connectorx is not available.
"""
from __future__ import annotations

import logging
import os
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
