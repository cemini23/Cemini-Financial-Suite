"""Cemini Financial Suite — Bull Agent (Step 47).

Phase 2 (ARGUING): Constructs the bullish case by reading macro context
from the blackboard and tallying confirming positive signals.

Deterministic confidence: `base + confirming_signals * SIGNAL_WEIGHT`.
Higher confidence in GREEN regime, lower in RED.
"""
from __future__ import annotations

from datetime import datetime, timezone

from debate_protocol.agents.base import BaseAgent
from debate_protocol.config import BASE_CONFIDENCE, SIGNAL_CONFIRMING_WEIGHT
from debate_protocol.models import AgentArgument, AgentRole, CrossExamination, DebatePhase, DebateState, Rebuttal


class BullAgent(BaseAgent):
    """Argues FOR the trade — builds the strongest possible bullish case."""

    async def execute(self, state: DebateState) -> AgentArgument:
        ctx = state.macro_context
        regime = state.regime or ctx.get("regime", "YELLOW")
        regime_upper = regime.upper()

        confirming = 0
        evidence: dict = {"regime": regime}
        reasons: list[str] = []

        # ── Regime gives a base bias ───────────────────────────────────────────
        if regime_upper == "GREEN":
            confirming += 2
            reasons.append("GREEN regime: SPY above rising 21-day EMA — bull cycle active")
        elif regime_upper == "YELLOW":
            confirming += 1
            reasons.append("YELLOW regime: neutral — defensive but not in bear mode")
        else:
            reasons.append("RED regime: headwind noted — requires strong catalysts")

        # ── SPY trend ─────────────────────────────────────────────────────────
        spy_trend = ctx.get("spy_trend")
        if spy_trend == "bullish":
            confirming += 1
            reasons.append("SPY trend: bullish momentum confirmed")
            evidence["spy_trend"] = spy_trend

        # ── VIX — contrarian buy signal at extremes ────────────────────────────
        vix = ctx.get("vix_level", 20.0)
        if vix and float(vix) >= 40.0:
            confirming += 1
            reasons.append(f"VIX={vix:.1f} — extreme fear is a contrarian buy signal")
            evidence["vix_contrarian"] = True
        elif vix and float(vix) <= 18.0:
            confirming += 1
            reasons.append(f"VIX={vix:.1f} — low volatility supports trend continuation")

        # ── Yield curve ───────────────────────────────────────────────────────
        spread = ctx.get("yield_curve_spread")
        if spread is not None and float(spread) > 0.5:
            confirming += 1
            reasons.append(f"Yield curve spread={spread:.2f}% — positive, supports growth")
            evidence["yield_curve"] = spread

        # ── Social sentiment ──────────────────────────────────────────────────
        social = ctx.get("social_score", 0.0)
        if social and float(social) > 0.3:
            confirming += 1
            reasons.append(f"Social sentiment={social:.2f} — positive retail/news flow")
            evidence["social_score"] = social

        # ── EDGAR insider cluster ─────────────────────────────────────────────
        edgar_type = ctx.get("edgar_alert_type", "")
        if edgar_type == "insider_cluster":
            confirming += 2
            reasons.append("Insider buying cluster detected (Step 17) — insiders have skin in game")
            evidence["insider_cluster"] = True

        # ── Confidence calculation ─────────────────────────────────────────────
        # RED regime: cap bull confidence to avoid overconfidence
        conf = BASE_CONFIDENCE + confirming * SIGNAL_CONFIRMING_WEIGHT
        if regime_upper == "RED":
            conf = min(conf, 0.55)
        confidence = round(min(1.0, max(0.1, conf)), 3)

        reasoning = (
            f"Bullish case for {state.ticker} in {regime} regime. "
            + " ".join(reasons)
            + f" Confirming signals: {confirming}. Confidence: {confidence:.0%}."
        )

        return AgentArgument(
            agent=AgentRole.BULL,
            phase=DebatePhase.ARGUING,
            position="bullish",
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
        )

    async def rebut(self, state: DebateState, challenge: CrossExamination) -> Rebuttal:
        """Bull agent defends its position against a cross-examination."""
        ctx = state.macro_context
        regime = state.regime or ctx.get("regime", "YELLOW")
        original_arg = state.get_argument_by_role(AgentRole.BULL)
        original_conf = original_arg.confidence if original_arg else BASE_CONFIDENCE

        vulnerability = challenge.vulnerability
        severity = challenge.severity

        # Confidence drops proportionally to severity of challenge
        rebuttal_conf = round(max(0.1, original_conf - severity * 0.3), 3)

        if "regime" in vulnerability.lower() and regime.upper() == "RED":
            rebuttal_text = (
                f"Acknowledging RED regime headwind (severity={severity:.2f}). "
                "However, extreme fear creates contrarian opportunities. "
                "Position sizing is reduced accordingly — this is a high risk/reward trade."
            )
            rebuttal_conf = round(max(0.1, original_conf - severity * 0.4), 3)
        elif "single indicator" in vulnerability.lower() or "concentration" in vulnerability.lower():
            rebuttal_text = (
                "Multiple independent signals confirmed: regime + momentum + sentiment. "
                "Not relying on any single indicator. RSI is one of several confirming factors."
            )
        elif "insider" in vulnerability.lower():
            rebuttal_text = (
                "Insider data is incorporated as supporting evidence, not primary thesis. "
                "The primary case rests on macro and momentum signals."
            )
        else:
            rebuttal_text = (
                f"Challenge noted: {vulnerability}. "
                "Bull case acknowledges this risk but maintains conviction based on "
                "the preponderance of confirming signals."
            )

        return Rebuttal(
            agent=AgentRole.BULL,
            original_argument_id="bull",
            challenge_addressed=vulnerability,
            rebuttal_text=rebuttal_text,
            confidence_after_rebuttal=rebuttal_conf,
        )
