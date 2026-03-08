"""intelligence/vector_store.py — Core pgvector CRUD operations (Step 29c).

Provides insert, batch insert, similarity search, and stats against intel_embeddings.
Uses psycopg2 + pgvector Python package for vector type registration.

Killer feature: search_similar_with_market_context() JOINs intel_embeddings with
raw_market_ticks to return similar intel alongside the market state at that time.
This single SQL statement demonstrates the pgvector + TimescaleDB architectural advantage.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger("intelligence.vector_store")

# ── DB config (env-first) ─────────────────────────────────────────────────────
_DB_HOST = os.getenv("DB_HOST", "postgres")
_DB_PORT = int(os.getenv("DB_PORT", "5432"))
_DB_NAME = os.getenv("POSTGRES_DB", "qdb")
_DB_USER = os.getenv("POSTGRES_USER", "admin")
_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quest")  # nosemgrep: semgrep.hardcoded-env-default-credential


def _get_conn() -> psycopg2.extensions.connection:
    """Open a new psycopg2 connection with pgvector type registered."""
    from pgvector.psycopg2 import register_vector

    conn = psycopg2.connect(
        host=_DB_HOST,
        port=_DB_PORT,
        dbname=_DB_NAME,
        user=_DB_USER,
        password=_DB_PASSWORD,
    )
    register_vector(conn)
    return conn


def store_embedding(
    content: str,
    embedding: list[float],
    source_type: str,
    source_id: str | None = None,
    source_channel: str | None = None,
    metadata: dict | None = None,
    tickers: list[str] | None = None,
    timestamp: datetime | None = None,
) -> int:
    """Insert one embedding row. Returns the new row id."""
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                if timestamp is not None:
                    cur.execute(
                        """
                        INSERT INTO intel_embeddings
                            (timestamp, source_type, source_id, source_channel,
                             content, embedding, metadata, tickers)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                        RETURNING id
                        """,
                        (
                            timestamp,
                            source_type,
                            source_id,
                            source_channel,
                            content,
                            embedding,
                            json.dumps(metadata or {}),
                            tickers or [],
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO intel_embeddings
                            (source_type, source_id, source_channel,
                             content, embedding, metadata, tickers)
                        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                        RETURNING id
                        """,
                        (
                            source_type,
                            source_id,
                            source_channel,
                            content,
                            embedding,
                            json.dumps(metadata or {}),
                            tickers or [],
                        ),
                    )
                row_id: int = cur.fetchone()[0]
        return row_id
    finally:
        conn.close()


def store_embeddings_batch(records: list[dict]) -> int:
    """Bulk insert records using execute_values for efficiency.

    Each record dict must have: content, embedding, source_type.
    Optional keys: source_id, source_channel, metadata, tickers, timestamp.

    Uses ON CONFLICT DO NOTHING on the (source_type, source_id) partial unique index
    to make the seeder idempotent when source_id is provided.

    Returns count of rows inserted.
    """
    if not records:
        return 0

    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                rows = [
                    (
                        r.get("timestamp"),
                        r["source_type"],
                        r.get("source_id"),
                        r.get("source_channel"),
                        r["content"],
                        r["embedding"],
                        json.dumps(r.get("metadata") or {}),
                        r.get("tickers") or [],
                    )
                    for r in records
                ]
                execute_values(
                    cur,
                    """
                    INSERT INTO intel_embeddings
                        (timestamp, source_type, source_id, source_channel,
                         content, embedding, metadata, tickers)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    rows,
                    template="(%s, %s, %s, %s, %s, %s::vector, %s::jsonb, %s)",
                )
                return cur.rowcount
    finally:
        conn.close()


def search_similar(
    query_embedding: list[float],
    limit: int = 10,
    source_type: str | None = None,
    tickers: list[str] | None = None,
    since: datetime | None = None,
    min_similarity: float = 0.5,
) -> list[dict]:
    """Find documents most similar to query_embedding using cosine similarity.

    Uses HNSW index with ef_search quality setting.
    Returns list of dicts sorted by similarity_score descending.
    """
    from intelligence.config import VECTOR_SEARCH_EF

    wheres: list[str] = ["1 - (embedding <=> %s::vector) >= %s"]
    params_where: list[Any] = [query_embedding, min_similarity]

    if source_type is not None:
        wheres.append("source_type = %s")
        params_where.append(source_type)

    if tickers:
        wheres.append("tickers && %s")
        params_where.append(tickers)

    if since is not None:
        wheres.append("timestamp >= %s")
        params_where.append(since)

    where_clause = " AND ".join(wheres)
    sql = f"""
        SELECT
            id, content, source_type, source_id, source_channel,
            1 - (embedding <=> %s::vector) AS similarity_score,
            metadata, tickers, timestamp
        FROM intel_embeddings
        WHERE {where_clause}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    # Params: [vec for score], [where filters...], [vec for ORDER BY], [limit]
    all_params: list[Any] = [query_embedding] + params_where + [query_embedding, limit]

    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL hnsw.ef_search = {int(VECTOR_SEARCH_EF)}")  # noqa: S608
                cur.execute(sql, all_params)
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "content": r[1],
                "source_type": r[2],
                "source_id": r[3],
                "source_channel": r[4],
                "similarity_score": float(r[5]),
                "metadata": r[6] if isinstance(r[6], dict) else json.loads(r[6] or "{}"),
                "tickers": list(r[7] or []),
                "timestamp": r[8],
            }
            for r in rows
        ]
    finally:
        conn.close()


def search_similar_with_market_context(
    query_embedding: list[float],
    limit: int = 10,
    tickers: list[str] | None = None,
) -> list[dict]:
    """pgvector + TimescaleDB killer query.

    Finds semantically similar intel AND JOINs with raw_market_ticks to return
    the market state (close, volume, rsi) at the time that intel was published.

    This is the query that demonstrates the architectural advantage of pgvector
    on the same Postgres instance as the time-series data — no dedicated vector
    DB can do this JOIN in a single statement.
    """
    from intelligence.config import VECTOR_SEARCH_EF

    ticker_filter = ""
    params: list[Any] = [query_embedding]

    if tickers:
        ticker_filter = "AND ie.tickers && %s"
        params.append(tickers)

    params.append(query_embedding)
    params.append(limit)

    sql = f"""
        SELECT
            ie.id,
            ie.content,
            ie.source_type,
            ie.source_id,
            1 - (ie.embedding <=> %s::vector) AS similarity_score,
            ie.metadata,
            ie.tickers,
            ie.timestamp,
            rmt.close     AS market_close,
            rmt.volume    AS market_volume,
            rmt.rsi       AS market_rsi,
            rmt.ticker    AS market_ticker
        FROM intel_embeddings ie
        LEFT JOIN LATERAL (
            SELECT close, volume, rsi, ticker
            FROM raw_market_ticks
            WHERE timestamp <= ie.timestamp
              AND (
                  array_length(ie.tickers, 1) IS NULL
                  OR ticker = ANY(ie.tickers)
              )
            ORDER BY timestamp DESC
            LIMIT 1
        ) rmt ON true
        WHERE 1=1 {ticker_filter}
        ORDER BY ie.embedding <=> %s::vector
        LIMIT %s
    """

    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL hnsw.ef_search = {int(VECTOR_SEARCH_EF)}")  # noqa: S608
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "content": r[1],
                "source_type": r[2],
                "source_id": r[3],
                "similarity_score": float(r[4]),
                "metadata": r[5] if isinstance(r[5], dict) else json.loads(r[5] or "{}"),
                "tickers": list(r[6] or []),
                "timestamp": r[7],
                "market_state": (
                    {"close": r[8], "volume": r[9], "rsi": r[10], "ticker": r[11]}
                    if r[8] is not None
                    else None
                ),
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_embedding_by_source(source_type: str, source_id: str) -> dict | None:
    """Fetch a single embedding by (source_type, source_id) for /similar lookup."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, source_type, source_id, embedding FROM intel_embeddings "
                "WHERE source_type = %s AND source_id = %s LIMIT 1",
                (source_type, source_id),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return {"id": row[0], "content": row[1], "source_type": row[2], "source_id": row[3], "embedding": row[4]}
    finally:
        conn.close()


def get_stats() -> dict:
    """Return embedding stats: total, by source type, oldest, newest, avg_per_day."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM intel_embeddings")
            total: int = cur.fetchone()[0]

            cur.execute(
                "SELECT source_type, COUNT(*) FROM intel_embeddings "
                "GROUP BY source_type ORDER BY 2 DESC"
            )
            by_source: dict[str, int] = {row[0]: row[1] for row in cur.fetchall()}

            cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM intel_embeddings")
            oldest, newest = cur.fetchone()

        avg_per_day = 0.0
        if oldest and newest and oldest != newest:
            delta_days = (newest - oldest).total_seconds() / 86400
            avg_per_day = round(total / max(delta_days, 1), 1)

        return {
            "total_embeddings": total,
            "by_source_type": by_source,
            "oldest": oldest.isoformat() if oldest else None,
            "newest": newest.isoformat() if newest else None,
            "avg_per_day": avg_per_day,
        }
    finally:
        conn.close()
