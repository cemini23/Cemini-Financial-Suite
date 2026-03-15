"""Cemini Financial Suite — Human-in-the-Loop Approval Gate (Step 49e).

For high-confidence signals above a configurable threshold, the system
pauses execution and waits for human approval via a Redis approval queue.
If no response arrives within HITL_TIMEOUT_SECONDS the order is auto-rejected
(fail-safe default).

Workflow:
  1. request_approval(signal_id, details) → publishes to safety:hitl:pending queue
  2. Optionally posts a Discord alert (DISCORD_WEBHOOK_URL env var)
  3. wait_for_decision(signal_id, timeout) → polls safety:hitl:decision:{id}
  4. Operator approves/rejects by writing to safety:hitl:decision:{id} via CLI/UI
  5. Auto-reject if timeout expires

Redis keys:
  safety:hitl:pending            LIST  — LPUSH pending approvals (TTL via item age check)
  safety:hitl:decision:{id}      STRING — "APPROVE" | "REJECT" (TTL = HITL_TIMEOUT_SECONDS)

Env vars:
  HITL_TIMEOUT_SECONDS   default 300
  HITL_CONFIDENCE_FLOOR  default 0.85  (only signals above this need HITL)
  DISCORD_WEBHOOK_URL    optional
"""
from __future__ import annotations

import json
import logging
import os
import time
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("shared.safety.hitl_gate")

_PENDING_KEY = "safety:hitl:pending"
_DECISION_KEY_PREFIX = "safety:hitl:decision:"
_DEFAULT_TIMEOUT = 300          # 5 minutes
_DEFAULT_FLOOR = 0.85
_POLL_INTERVAL = 0.5            # seconds between Redis polls


class HITLDecision(str, Enum):
    APPROVED = "APPROVE"
    REJECTED = "REJECT"
    TIMEOUT = "TIMEOUT"         # auto-reject after timeout
    SKIPPED = "SKIPPED"         # confidence below floor — no HITL needed


class HITLGate:
    """Human-in-the-Loop approval gate.

    Args:
        redis_client:        Sync Redis client.
        confidence_floor:    Signals at or above this require human approval.
        timeout_seconds:     How long to wait before auto-rejecting.
    """

    def __init__(
        self,
        redis_client,
        confidence_floor: float = _DEFAULT_FLOOR,
        timeout_seconds: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self.redis = redis_client
        self.confidence_floor = confidence_floor
        self.timeout_seconds = timeout_seconds

    # ── Public interface ────────────────────────────────────────────────────

    def requires_approval(self, confidence: float) -> bool:
        """Return True if this confidence level triggers HITL."""
        return confidence >= self.confidence_floor

    def request_approval(
        self,
        signal_id: str,
        details: dict[str, Any],
    ) -> None:
        """Push an approval request onto the pending queue and alert Discord."""
        payload = {
            "signal_id": signal_id,
            "details": details,
            "requested_at": time.time(),
            "timeout_at": time.time() + self.timeout_seconds,
        }
        try:
            self.redis.lpush(_PENDING_KEY, json.dumps(payload))
            logger.info(
                "🔔 HITL: approval requested — signal_id=%s ticker=%s action=%s",
                signal_id,
                details.get("ticker", "?"),
                details.get("action", "?"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("HITL: request_approval Redis error: %s", exc)

        # Best-effort Discord alert
        self._send_discord_alert(signal_id, details)

    def wait_for_decision(
        self,
        signal_id: str,
        timeout: Optional[int] = None,
    ) -> HITLDecision:
        """Block until operator approves/rejects or timeout expires.

        Args:
            signal_id: The unique signal identifier from request_approval().
            timeout:   Override the instance-level timeout (seconds).

        Returns:
            HITLDecision enum value.
        """
        deadline = time.time() + (timeout or self.timeout_seconds)
        key = f"{_DECISION_KEY_PREFIX}{signal_id}"

        while time.time() < deadline:
            try:
                val = self.redis.get(key)
                if val:
                    decision_str = val.upper() if isinstance(val, str) else val.decode().upper()
                    if decision_str == "APPROVE":
                        logger.info("✅ HITL: APPROVED — signal_id=%s", signal_id)
                        return HITLDecision.APPROVED
                    else:
                        logger.warning("🚫 HITL: REJECTED — signal_id=%s", signal_id)
                        return HITLDecision.REJECTED
            except Exception as exc:  # noqa: BLE001
                logger.warning("HITL: poll error (%s)", exc)

            time.sleep(_POLL_INTERVAL)

        logger.warning(
            "⏰ HITL: TIMEOUT — signal_id=%s auto-rejected after %ds",
            signal_id, timeout or self.timeout_seconds,
        )
        return HITLDecision.TIMEOUT

    def submit_decision(self, signal_id: str, decision: HITLDecision) -> None:
        """Operator or test helper: write a decision to Redis.

        Args:
            signal_id: Signal to approve/reject.
            decision:  HITLDecision.APPROVED or HITLDecision.REJECTED.
        """
        key = f"{_DECISION_KEY_PREFIX}{signal_id}"
        try:
            self.redis.set(key, decision.value, ex=self.timeout_seconds)
            logger.info("HITL: decision written — signal_id=%s decision=%s", signal_id, decision.value)
        except Exception as exc:  # noqa: BLE001
            logger.warning("HITL: submit_decision failed: %s", exc)

    def evaluate(
        self,
        signal_id: str,
        confidence: float,
        details: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> HITLDecision:
        """Convenience: check floor, request if needed, then wait.

        If confidence < floor, returns HITLDecision.SKIPPED immediately.
        """
        if not self.requires_approval(confidence):
            return HITLDecision.SKIPPED

        self.request_approval(signal_id, details)
        return self.wait_for_decision(signal_id, timeout)

    # ── Private helpers ─────────────────────────────────────────────────────

    def _send_discord_alert(self, signal_id: str, details: dict[str, Any]) -> None:
        """Best-effort Discord webhook notification."""
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        if not webhook_url:
            return
        try:
            ticker = details.get("ticker", "?")
            action = details.get("action", "?")
            conf = details.get("confidence", 0.0)

            try:
                import sys as _sys
                import os as _os_inner
                _repo = _os_inner.path.abspath(
                    _os_inner.path.join(_os_inner.path.dirname(__file__), "..", "..")
                )
                if _repo not in _sys.path:
                    _sys.path.insert(0, _repo)
                from core.discord_notifier import DiscordNotifier  # noqa: N814
                notifier = DiscordNotifier(webhook_url=webhook_url, username="Cemini HITL Gate")
                notifier.send_alert(
                    f"🔔 HITL Approval Required: {ticker}",
                    f"Action: {action} | Signal ID: {signal_id}",
                    alert_type="WARNING",
                    ticker=str(ticker) if ticker != "?" else None,
                    enrich=True,
                    fields=[
                        {"name": "Confidence", "value": f"{conf:.1%}", "inline": True},
                        {"name": "Signal ID", "value": signal_id, "inline": False},
                        {"name": "Expires in", "value": f"{self.timeout_seconds}s", "inline": True},
                    ],
                )
                return
            except Exception:
                pass  # fall through to raw requests below

            import requests
            payload = {
                "embeds": [
                    {
                        "title": f"🔔 HITL Approval Required: {ticker}",
                        "color": 0xFFA500,
                        "fields": [
                            {"name": "Action", "value": str(action), "inline": True},
                            {"name": "Confidence", "value": f"{conf:.1%}", "inline": True},
                            {"name": "Signal ID", "value": signal_id, "inline": False},
                            {
                                "name": "Expires in",
                                "value": f"{self.timeout_seconds}s",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Set safety:hitl:decision:{id} to APPROVE or REJECT"},
                    }
                ]
            }
            resp = requests.post(webhook_url, json=payload, timeout=5)
            logger.debug("HITL Discord alert HTTP %s", resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.debug("HITL Discord alert failed (non-critical): %s", exc)
