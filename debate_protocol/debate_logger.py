"""Cemini Financial Suite — Debate Logger (Step 47).

Writes complete debate states to:
  1. Postgres debate_sessions table (JSONB payload)
  2. JSONL archive at /mnt/archive/debates/YYYY-MM-DD.jsonl
  3. Audit hash chain via shared.audit_trail.chain_writer
  4. Redis intel:debate_verdict (Intel Bus, TTL 1800s)

All methods fail silently — never raises, never blocks the caller.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from debate_protocol.config import ARCHIVE_ROOT_DEFAULT, DEBATE_VERDICT_TTL, INTEL_DEBATE_VERDICT
from debate_protocol.models import DebateState, DebateVerdictIntel

logger = logging.getLogger("debate_protocol.debate_logger")


def _archive_root() -> str:
    return os.getenv("DEBATE_ARCHIVE_DIR", ARCHIVE_ROOT_DEFAULT)


def _new_uuid() -> str:
    try:
        from uuid_utils import uuid7
        return str(uuid7())
    except ImportError:
        import uuid
        return str(uuid.uuid4())


def log_to_postgres(state: DebateState, conn) -> None:
    """Insert complete debate state into debate_sessions table."""
    if conn is None or state.verdict is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO debate_sessions
                    (id, ticker, regime, verdict, confidence, bull_score, bear_score,
                     tie_break_used, phase_count, payload, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    state.session_id,
                    state.ticker,
                    state.regime,
                    state.verdict.action,
                    state.verdict.confidence,
                    state.verdict.bull_score,
                    state.verdict.bear_score,
                    state.verdict.tie_break_used,
                    len(state.arguments),
                    json.dumps(state.model_dump(mode="json"), default=str),
                    state.started_at,
                    state.completed_at,
                ),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("debate_sessions INSERT failed: %s", exc)
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass


def log_to_jsonl(state: DebateState) -> None:
    """Append debate state to daily JSONL archive."""
    try:
        root = Path(_archive_root())
        root.mkdir(parents=True, exist_ok=True)
        ts = state.completed_at or state.started_at
        date_str = ts.strftime("%Y-%m-%d")
        path = root / f"{date_str}.jsonl"
        with path.open("a") as fh:
            fh.write(json.dumps(state.model_dump(mode="json"), default=str) + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Debate JSONL write failed: %s", exc)


def log_to_audit_chain(state: DebateState, conn=None) -> None:
    """Write debate verdict to cryptographic audit hash chain."""
    if state.verdict is None:
        return
    try:
        from shared.audit_trail.chain_writer import write_audit_entry
        write_audit_entry(
            source_table="debate_sessions",
            source_id=state.session_id,
            payload=state.model_dump(mode="json"),
            pg_conn=conn,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Audit chain write skipped: %s", exc)


def publish_verdict_intel(state: DebateState, redis_client=None) -> None:
    """Publish slim DebateVerdictIntel to intel:debate_verdict."""
    if state.verdict is None or redis_client is None:
        return
    try:
        verdict_intel = DebateVerdictIntel(
            session_id=state.session_id,
            ticker=state.ticker,
            action=state.verdict.action,
            confidence=state.verdict.confidence,
            regime=state.regime,
            bull_score=state.verdict.bull_score,
            bear_score=state.verdict.bear_score,
            tie_break_used=state.verdict.tie_break_used,
            summary=state.verdict.reasoning[:200],
        )
        envelope = json.dumps({
            "value": verdict_intel.model_dump(mode="json"),
            "source_system": "debate_protocol",
            "timestamp": time.time(),
            "confidence": state.verdict.confidence,
        }, default=str)
        redis_client.set(INTEL_DEBATE_VERDICT, envelope, ex=DEBATE_VERDICT_TTL)
        logger.info("Published intel:debate_verdict for %s action=%s", state.ticker, state.verdict.action)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Verdict intel publish failed: %s", exc)


def log_debate(state: DebateState, conn=None, redis_client=None) -> None:
    """Full logging: Postgres + JSONL + audit chain + Intel Bus."""
    log_to_postgres(state, conn)
    log_to_jsonl(state)
    log_to_audit_chain(state, conn)
    publish_verdict_intel(state, redis_client)
