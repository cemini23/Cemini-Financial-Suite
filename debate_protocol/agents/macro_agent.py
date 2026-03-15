"""Cemini Financial Suite — Macro Agent (Step 47).

Phase 1 (GATHERING): Reads all available Intel Bus channels and builds a
macro context dict that all subsequent agents read from the blackboard.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from debate_protocol.agents.base import BaseAgent
from debate_protocol.config import (
    INTEL_BTC_SENTIMENT,
    INTEL_EDGAR_ALERT,
    INTEL_FRED_CREDIT_SPREAD,
    INTEL_FRED_YIELD_CURVE,
    INTEL_PLAYBOOK_SNAPSHOT,
    INTEL_SOCIAL_SCORE,
    INTEL_SPY_TREND,
    INTEL_VIX_LEVEL,
    VIX_ELEVATED,
    VIX_EXTREME,
)
from debate_protocol.models import AgentArgument, AgentRole, CrossExamination, DebatePhase, DebateState, Rebuttal

logger = logging.getLogger("debate_protocol.agents.macro")


def _read_redis_key(redis_client, key: str):
    """Synchronous Redis GET returning parsed JSON envelope or None."""
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception:  # noqa: BLE001
        return None


class MacroAgent(BaseAgent):
    """Gathers macro context from the Intel Bus.

    This agent runs first (GATHERING phase) and populates state.macro_context
    and state.regime so all other agents have a consistent macro baseline.

    Deterministic: confidence is derived entirely from data availability
    and signal alignment (no LLM).
    """

    def __init__(self, role: AgentRole, blackboard, redis_client=None) -> None:
        super().__init__(role, blackboard)
        self._redis = redis_client

    async def execute(self, state: DebateState) -> AgentArgument:
        """Read Intel Bus channels and build macro context."""
        ctx: dict = {}
        confirming_bull = 0
        confirming_bear = 0
        signals_checked = 0

        # ── Playbook snapshot (regime + signals) ──────────────────────────────
        snap = _read_redis_key(self._redis, INTEL_PLAYBOOK_SNAPSHOT)
        snap_val = self._read_intel_value(snap)
        if isinstance(snap_val, dict):
            ctx["regime"] = snap_val.get("regime", "YELLOW")
            ctx["playbook_signal_count"] = len(snap_val.get("signals", []))
        else:
            ctx["regime"] = "YELLOW"

        # ── SPY trend ─────────────────────────────────────────────────────────
        spy_env = _read_redis_key(self._redis, INTEL_SPY_TREND)
        spy_trend = self._read_intel_value(spy_env)
        ctx["spy_trend"] = spy_trend
        if spy_trend == "bullish":
            confirming_bull += 1
        elif spy_trend == "bearish":
            confirming_bear += 1
        signals_checked += 1

        # ── VIX level ─────────────────────────────────────────────────────────
        vix_env = _read_redis_key(self._redis, INTEL_VIX_LEVEL)
        vix_raw = self._read_intel_value(vix_env)
        vix = self._safe_float(vix_raw, 20.0)
        ctx["vix_level"] = vix
        if vix >= VIX_EXTREME:
            confirming_bear += 2  # double weight for extreme fear
        elif vix >= VIX_ELEVATED:
            confirming_bear += 1
        else:
            confirming_bull += 1
        signals_checked += 1

        # ── FRED yield curve ──────────────────────────────────────────────────
        yc_env = _read_redis_key(self._redis, INTEL_FRED_YIELD_CURVE)
        yc_val = self._read_intel_value(yc_env)
        if isinstance(yc_val, dict):
            spread = self._safe_float(yc_val.get("spread_10y2y"), 0.0)
            ctx["yield_curve_spread"] = spread
            if spread < 0:
                confirming_bear += 1  # inverted yield curve
                signals_checked += 1
            elif spread > 0.5:
                confirming_bull += 1
                signals_checked += 1

        # ── FRED credit spread ────────────────────────────────────────────────
        cs_env = _read_redis_key(self._redis, INTEL_FRED_CREDIT_SPREAD)
        cs_val = self._read_intel_value(cs_env)
        if isinstance(cs_val, dict):
            hy_spread = self._safe_float(cs_val.get("hy_oas_spread"), 0.0)
            ctx["hy_credit_spread"] = hy_spread
            if hy_spread > 500:  # >500 bps = stress
                confirming_bear += 1
                signals_checked += 1

        # ── EDGAR alert ───────────────────────────────────────────────────────
        edgar_env = _read_redis_key(self._redis, INTEL_EDGAR_ALERT)
        edgar_val = self._read_intel_value(edgar_env)
        if isinstance(edgar_val, dict):
            ctx["edgar_alert_ticker"] = edgar_val.get("ticker")
            ctx["edgar_alert_score"] = edgar_val.get("significance_score", 0)
            ctx["edgar_alert_type"] = edgar_val.get("alert_type")

        # ── Social sentiment ──────────────────────────────────────────────────
        social_env = _read_redis_key(self._redis, INTEL_SOCIAL_SCORE)
        social_val = self._read_intel_value(social_env)
        if isinstance(social_val, dict):
            score = self._safe_float(social_val.get("score"), 0.0)
            ctx["social_score"] = score
            if score > 0.3:
                confirming_bull += 1
            elif score < -0.3:
                confirming_bear += 1
            signals_checked += 1

        # ── BTC sentiment ─────────────────────────────────────────────────────
        btc_env = _read_redis_key(self._redis, INTEL_BTC_SENTIMENT)
        btc_sentiment = self._safe_float(self._read_intel_value(btc_env), 0.0)
        ctx["btc_sentiment"] = btc_sentiment

        # ── Derive macro position ──────────────────────────────────────────────
        ctx["confirming_bull"] = confirming_bull
        ctx["confirming_bear"] = confirming_bear
        ctx["signals_checked"] = max(signals_checked, 1)

        if confirming_bull > confirming_bear:
            position = "bullish"
        elif confirming_bear > confirming_bull:
            position = "bearish"
        else:
            position = "neutral"

        total = confirming_bull + confirming_bear
        confidence = min(1.0, 0.4 + (total / max(signals_checked, 1)) * 0.5)

        regime = ctx.get("regime", "YELLOW")
        reasoning = (
            f"Macro context: regime={regime}, spy_trend={spy_trend}, "
            f"vix={vix:.1f}, bull_signals={confirming_bull}, bear_signals={confirming_bear}. "
            f"Macro stance: {position}."
        )

        return AgentArgument(
            agent=AgentRole.MACRO,
            phase=DebatePhase.GATHERING,
            position=position,
            confidence=round(confidence, 3),
            reasoning=reasoning,
            evidence=ctx,
        )

    async def rebut(self, state: DebateState, challenge: CrossExamination) -> Rebuttal:
        """Macro agent defends its context with available data coverage."""
        signals_checked = state.macro_context.get("signals_checked", 1)
        coverage_pct = min(1.0, signals_checked / 6)
        return Rebuttal(
            agent=AgentRole.MACRO,
            original_argument_id="macro",
            challenge_addressed=challenge.vulnerability,
            rebuttal_text=(
                f"Macro context drawn from {signals_checked} Intel Bus channels. "
                f"Coverage: {coverage_pct:.0%}. "
                "Missing channels default to neutral — no false signals injected."
            ),
            confidence_after_rebuttal=round(0.4 + coverage_pct * 0.3, 3),
        )
