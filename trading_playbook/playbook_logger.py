"""
Cemini Financial Suite — Playbook Logger

Bridges the playbook layer to the RL training pipeline.

Writes every regime snapshot, detected signal, and risk metric to:
  1. Postgres ``playbook_logs`` table (queryable, durable).
  2. JSONL files on disk under ``/mnt/archive/playbook/YYYY-MM-DD/``
     (one file per hour, rotated automatically — easy to feed into a
     PyTorch / TF Dataset loader).
  3. Redis Intel Bus key ``intel:playbook_snapshot`` (latest state for
     real-time consumers; 5-minute TTL).

Log record schema
-----------------
{
    "timestamp":  <float epoch>,
    "log_type":   "regime" | "signal" | "risk" | "kill_switch",
    "regime":     <str "GREEN"/"YELLOW"/"RED" or null>,
    "payload":    <dict — type-specific data>
}

The RL agent will consume regime + signals + risk state from these records
as part of its observation space.  This logger is additive — it never
modifies or interrupts the existing harvesters.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("playbook.logger")

# ----- optional deps -------------------------------------------------------- #
try:
    import psycopg2
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False
    logger.warning("[PlaybookLogger] psycopg2 not available — Postgres logging disabled")

try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

# ----- constants ------------------------------------------------------------ #
ARCHIVE_ROOT = os.getenv("PLAYBOOK_ARCHIVE_DIR", "/mnt/archive/playbook")
INTEL_KEY = "intel:playbook_snapshot"
INTEL_TTL = 300   # 5 minutes

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS playbook_logs (
    id         BIGSERIAL PRIMARY KEY,
    timestamp  TIMESTAMP WITH TIME ZONE NOT NULL,
    log_type   VARCHAR(50) NOT NULL,
    regime     VARCHAR(20),
    payload    JSONB NOT NULL
);
"""

_INSERT_SQL = """
INSERT INTO playbook_logs (timestamp, log_type, regime, payload)
VALUES (%s, %s, %s, %s)
"""


# ----- helpers -------------------------------------------------------------- #
def _pg_conn():
    """Return a new psycopg2 connection using env-sourced params."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "quest"),
        database=os.getenv("POSTGRES_DB", "qdb"),
    )


def _redis_client():
    """Return a sync Redis client."""
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return _redis_lib.Redis(
        host=host, port=6379, password=password,
        decode_responses=True, socket_connect_timeout=2,
    )


def _hour_key() -> str:
    """Return current UTC hour string for file naming: YYYY-MM-DD_HH."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H")


def _date_dir() -> str:
    """Return current UTC date string for directory naming: YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ============================================================================
# PlaybookLogger
# ============================================================================
class PlaybookLogger:
    """
    Structured logger for the playbook layer.

    All write operations fail silently — the logger must never crash the
    runner loop.

    Parameters
    ----------
    archive_root : str
        Root directory for JSONL archives.  Defaults to PLAYBOOK_ARCHIVE_DIR
        env var or ``/mnt/archive/playbook``.
    enable_postgres : bool
        Write to Postgres.  Requires psycopg2 and a reachable DB.
    enable_redis : bool
        Publish latest snapshot to Redis Intel Bus.
    enable_disk : bool
        Write JSONL files to archive_root.
    """

    def __init__(
        self,
        archive_root: str = ARCHIVE_ROOT,
        enable_postgres: bool = True,
        enable_redis: bool = True,
        enable_disk: bool = True,
    ):
        self.archive_root = archive_root
        self.enable_postgres = enable_postgres and _PG_AVAILABLE
        self.enable_redis = enable_redis and _REDIS_AVAILABLE
        self.enable_disk = enable_disk

        self._pg_conn = None
        self._pg_cursor = None

        if self.enable_postgres:
            self._connect_postgres()

    # ---------------------------------------------------------------------- #
    # Postgres setup
    # ---------------------------------------------------------------------- #
    def _connect_postgres(self) -> None:
        """Open a Postgres connection and ensure the table exists."""
        try:
            self._pg_conn = _pg_conn()
            self._pg_conn.autocommit = True
            self._pg_cursor = self._pg_conn.cursor()
            self._pg_cursor.execute(_CREATE_TABLE_SQL)
            logger.info("[PlaybookLogger] Connected to Postgres — playbook_logs ready")
        except Exception as exc:
            logger.warning("[PlaybookLogger] Postgres connection failed: %s", exc)
            self.enable_postgres = False
            self._pg_conn = None
            self._pg_cursor = None

    def _pg_write(self, log_type: str, regime: Optional[str], payload: dict) -> None:
        """Insert one record into playbook_logs.  Reconnects on failure."""
        if not self.enable_postgres:
            return
        try:
            ts = datetime.now(timezone.utc)
            self._pg_cursor.execute(_INSERT_SQL, (ts, log_type, regime, json.dumps(payload)))
        except Exception as exc:
            logger.warning("[PlaybookLogger] Postgres write failed: %s — reconnecting", exc)
            try:
                self._connect_postgres()
            except Exception:
                pass

    # ---------------------------------------------------------------------- #
    # Disk (JSONL)
    # ---------------------------------------------------------------------- #
    def _disk_write(self, record: dict) -> None:
        """Append *record* as a JSON line to the current hourly archive file."""
        if not self.enable_disk:
            return
        try:
            date_dir = Path(self.archive_root) / _date_dir()
            date_dir.mkdir(parents=True, exist_ok=True)
            fpath = date_dir / f"playbook_{_hour_key()}.jsonl"
            with fpath.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except Exception as exc:
            logger.debug("[PlaybookLogger] Disk write failed: %s", exc)

    # ---------------------------------------------------------------------- #
    # Redis publish
    # ---------------------------------------------------------------------- #
    def _redis_publish(self, payload: dict) -> None:
        """Set INTEL_KEY on the Intel Bus with a 5-minute TTL."""
        if not self.enable_redis:
            return
        try:
            r = _redis_client()
            r.set(INTEL_KEY, json.dumps({
                "value": payload,
                "source_system": "playbook_logger",
                "timestamp": time.time(),
                "confidence": 1.0,
            }), ex=INTEL_TTL)
            r.close()
        except Exception as exc:
            logger.debug("[PlaybookLogger] Redis publish failed: %s", exc)

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #
    def _write(self, log_type: str, regime: Optional[str], payload: dict) -> None:
        """Central dispatch — writes to all enabled backends."""
        record: dict[str, Any] = {
            "timestamp": time.time(),
            "log_type": log_type,
            "regime": regime,
            "payload": payload,
        }
        self._pg_write(log_type, regime, payload)
        self._disk_write(record)

    def log_regime(self, regime_state) -> None:
        """
        Persist a RegimeState snapshot.

        Parameters
        ----------
        regime_state : RegimeState
            Output of ``macro_regime.classify_regime()``.
        """
        payload = regime_state.to_dict() if hasattr(regime_state, "to_dict") else dict(regime_state)
        self._write("regime", payload.get("regime"), payload)
        self._redis_publish({"regime": payload.get("regime"), "detail": payload})
        logger.debug("[PlaybookLogger] Logged regime: %s", payload.get("regime"))

    def log_signal(self, signal: dict) -> None:
        """
        Persist a detected signal from the signal catalog.

        Parameters
        ----------
        signal : dict
            Dict returned by a BaseSetup.detect() call.
        """
        regime = signal.get("regime_at_detection")   # optionally annotated by runner
        self._write("signal", regime, signal)
        self._redis_publish({"latest_signal": signal})
        logger.debug("[PlaybookLogger] Logged signal: %s on %s", signal.get("pattern_name"), signal.get("symbol"))

    def log_risk_snapshot(
        self,
        cvar: float,
        kelly_size: float,
        drawdown_snapshot: dict,
        nav: float = 0.0,
        regime: Optional[str] = None,
    ) -> None:
        """
        Persist a risk metrics snapshot.

        Parameters
        ----------
        cvar             : float  Current 99 % CVaR (negative = loss).
        kelly_size       : float  Current fractional Kelly position size.
        drawdown_snapshot: dict   From DrawdownMonitor.snapshot().
        nav              : float  Net Asset Value at snapshot time.
        regime           : str    Current macro regime label.
        """
        payload = {
            "cvar_99": round(float(cvar), 6),
            "kelly_size": round(float(kelly_size), 6),
            "nav": round(float(nav), 2),
            "drawdown_snapshot": drawdown_snapshot,
        }
        self._write("risk", regime, payload)
        logger.debug("[PlaybookLogger] Logged risk snapshot: CVaR=%.4f Kelly=%.4f", cvar, kelly_size)

    def log_kill_switch_event(self, event: dict) -> None:
        """
        Persist a kill-switch trigger or strategy halt event.

        Parameters
        ----------
        event : dict
            Typically from KillSwitch.state_snapshot() or the structured
            event dict published by KillSwitch._publish_to_redis().
        """
        self._write("kill_switch", None, event)
        logger.warning("[PlaybookLogger] Logged kill_switch event: %s", event.get("event", "unknown"))

    def log_raw(self, log_type: str, payload: dict, regime: Optional[str] = None) -> None:
        """
        Generic log entry.  Use for any playbook event not covered above.
        """
        self._write(log_type, regime, payload)

    def close(self) -> None:
        """Close open database connections cleanly."""
        if self._pg_conn:
            try:
                self._pg_conn.close()
            except Exception:
                pass
            self._pg_conn = None
            self._pg_cursor = None
