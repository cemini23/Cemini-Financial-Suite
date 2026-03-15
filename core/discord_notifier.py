"""Cemini Financial Suite — Centralized Discord Notifier (Step 36).

Single module all services import instead of raw webhook POST calls.
Adds intel enrichment (regime, sector rotation, earnings cluster, VIX)
to Discord embeds automatically.

Features
--------
- DISCORD_ALERTS_ENABLED env guard (default: true)
- Rate limiting: 2-second minimum gap between sends (in-memory, per-instance)
- Intel enrichment from playbook_snapshot, sector_rotation, earnings_calendar, vix_level
- Clean embed format with alert-type colour coding
- Fail-silent: send_alert() never raises

Alert types and colours
-----------------------
  SIGNAL        → green  (#2ecc71)
  TRADE         → green  (#2ecc71)
  WARNING       → yellow (#f1c40f)
  CRITICAL      → red    (#e74c3c)
  INFO          → blue   (#3498db)
  REGIME_CHANGE → purple (#9b59b6)

Usage
-----
  from core.discord_notifier import get_notifier

  notifier = get_notifier()
  notifier.send_alert("Trade Placed", "NVDA BUY at $800",
                      alert_type="TRADE", ticker="NVDA")
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import requests

from core.intel_bus import IntelReader

logger = logging.getLogger("core.discord_notifier")

_RATE_LIMIT_SECONDS = 2.0

ALERT_COLORS: dict[str, int] = {
    "SIGNAL": 3066993,         # #2ecc71 green
    "TRADE": 3066993,          # #2ecc71 green
    "WARNING": 15844367,       # #f1c40f yellow
    "CRITICAL": 15158332,      # #e74c3c red
    "INFO": 3447003,           # #3498db blue
    "REGIME_CHANGE": 10181046, # #9b59b6 purple
}


def _alerts_enabled() -> bool:
    """Check DISCORD_ALERTS_ENABLED env var (default: enabled)."""
    return os.getenv("DISCORD_ALERTS_ENABLED", "true").lower() not in ("false", "0", "no")


class DiscordNotifier:
    """Centralized Discord webhook notifier with intel context enrichment.

    Each instance maintains its own rate-limit counter (2-second floor).
    All methods fail silently — never raises, never blocks the caller.
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        username: str = "Cemini OS",
    ) -> None:
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.username = username
        self._last_sent: float = 0.0

    def send_alert(
        self,
        title: str,
        message: str,
        alert_type: str = "INFO",
        ticker: Optional[str] = None,
        enrich: bool = True,
        fields: Optional[list[dict]] = None,
    ) -> bool:
        """Send a Discord embed alert.

        Returns True if the webhook returned HTTP 200/204, False otherwise.
        Never raises.

        Args:
            title:      Embed title.
            message:    Embed description / body text.
            alert_type: One of SIGNAL / TRADE / WARNING / CRITICAL / INFO / REGIME_CHANGE.
            ticker:     Optional equity symbol — added as first field if provided.
            enrich:     If True, read Intel Bus for regime/rotation/earnings/VIX context.
            fields:     Additional Discord embed fields appended after enrichment fields.
        """
        if not _alerts_enabled():
            return False
        if not self.webhook_url:
            return False
        if not self._rate_ok():
            logger.debug("[DiscordNotifier] rate-limited, skipping '%s'", title)
            return False

        context = self._gather_context(ticker) if enrich else {}
        embed = self._build_embed(title, message, alert_type, context, ticker, fields)
        payload = {"username": self.username, "embeds": [embed]}

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=5)
            self._last_sent = time.monotonic()
            logger.debug("[DiscordNotifier] sent '%s' HTTP %s", title, resp.status_code)
            return resp.status_code in (200, 204)
        except Exception as exc:
            logger.debug("[DiscordNotifier] HTTP failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rate_ok(self) -> bool:
        return (time.monotonic() - self._last_sent) >= _RATE_LIMIT_SECONDS

    def _gather_context(self, ticker: Optional[str] = None) -> dict[str, Any]:
        """Read regime/rotation/earnings/vix from Intel Bus.

        Always returns a dict — never raises.
        """
        ctx: dict[str, Any] = {}

        # Regime from playbook snapshot
        try:
            snap = IntelReader.read("intel:playbook_snapshot")
            if snap:
                val = snap.get("value", {})
                regime = str(val.get("regime", "")).upper()
                if regime:
                    ctx["regime"] = regime
                spy = val.get("spy_price")
                if spy is not None:
                    ctx["spy_price"] = spy
        except Exception:
            pass

        # Sector rotation bias
        try:
            sr = IntelReader.read("intel:sector_rotation")
            if sr:
                val = sr.get("value", {})
                rotation = val.get("rotation_bias")
                if rotation:
                    ctx["rotation_bias"] = rotation
        except Exception:
            pass

        # Earnings cluster / ticker proximity
        try:
            ec = IntelReader.read("intel:earnings_calendar")
            if ec:
                val = ec.get("value", {})
                ctx["earnings_cluster"] = bool(val.get("earnings_cluster", False))
                if ticker:
                    reporting = set(
                        val.get("reporting_this_week", [])
                        + val.get("reporting_soon", [])
                    )
                    ctx["ticker_near_earnings"] = ticker in reporting
        except Exception:
            pass

        # VIX level
        try:
            vix = IntelReader.read("intel:vix_level")
            if vix is not None:
                ctx["vix_level"] = vix.get("value")
        except Exception:
            pass

        return ctx

    def _build_embed(
        self,
        title: str,
        message: str,
        alert_type: str,
        context: dict[str, Any],
        ticker: Optional[str] = None,
        extra_fields: Optional[list[dict]] = None,
    ) -> dict:
        """Build a Discord embed dict from title, message, context, and extra fields."""
        color = ALERT_COLORS.get(alert_type.upper(), ALERT_COLORS["INFO"])
        fields: list[dict] = []

        if ticker:
            fields.append({"name": "Ticker", "value": ticker, "inline": True})

        regime = context.get("regime")
        if regime:
            fields.append({"name": "Regime", "value": regime, "inline": True})

        rotation = context.get("rotation_bias")
        if rotation:
            fields.append({"name": "Rotation", "value": rotation, "inline": True})

        vix = context.get("vix_level")
        if vix is not None:
            fields.append({"name": "VIX", "value": f"{vix:.1f}", "inline": True})

        if context.get("earnings_cluster"):
            fields.append({"name": "⚠️ Earnings Cluster", "value": "Active", "inline": True})

        if context.get("ticker_near_earnings"):
            fields.append({"name": "📅 Near Earnings", "value": str(ticker), "inline": True})

        if extra_fields:
            fields.extend(extra_fields)

        return {
            "title": title,
            "description": message,
            "color": color,
            "fields": fields,
            "footer": {"text": "Cemini Financial Suite"},
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_notifier: Optional[DiscordNotifier] = None


def get_notifier() -> DiscordNotifier:
    """Return (or create) the module-level singleton DiscordNotifier."""
    global _default_notifier
    if _default_notifier is None:
        _default_notifier = DiscordNotifier()
    return _default_notifier
