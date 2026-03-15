"""Cemini Financial Suite — Bear Agent (Step 47).

Phase 2 (ARGUING): Constructs the bearish case by reading macro context
from the blackboard and tallying confirming negative signals.

Deterministic confidence: `base + confirming_signals * SIGNAL_WEIGHT`.
Higher confidence in RED regime, lower in GREEN.
"""
from __future__ import annotations

from debate_protocol.agents.base import BaseAgent
from debate_protocol.config import BASE_CONFIDENCE, SIGNAL_CONFIRMING_WEIGHT, VIX_ELEVATED, VIX_EXTREME
from debate_protocol.models import AgentArgument, AgentRole, CrossExamination, DebatePhase, DebateState, Rebuttal


class BearAgent(BaseAgent):
    """Argues AGAINST the trade — builds the strongest possible bearish case."""

    async def execute(self, state: DebateState) -> AgentArgument:
        ctx = state.macro_context
        regime = state.regime or ctx.get("regime", "YELLOW")
        regime_upper = regime.upper()

        confirming = 0
        evidence: dict = {"regime": regime}
        reasons: list[str] = []

        # ── Regime bias ────────────────────────────────────────────────────────
        if regime_upper == "RED":
            confirming += 2
            reasons.append("RED regime: SPY below 50 SMA — survival mode, avoid new longs")
        elif regime_upper == "YELLOW":
            confirming += 1
            reasons.append("YELLOW regime: SPY below 21 EMA — defensive stance warranted")
        else:
            reasons.append("GREEN regime: headwind for bears — requires strong catalysts")

        # ── SPY trend ─────────────────────────────────────────────────────────
        spy_trend = ctx.get("spy_trend")
        if spy_trend == "bearish":
            confirming += 1
            reasons.append("SPY trend: bearish momentum confirmed")
            evidence["spy_trend"] = spy_trend

        # ── VIX elevated / trending higher ────────────────────────────────────
        vix = ctx.get("vix_level", 20.0)
        vix_f = float(vix) if vix else 20.0
        if vix_f >= VIX_EXTREME:
            confirming += 2
            reasons.append(f"VIX={vix_f:.1f} — panic levels, downside acceleration risk")
            evidence["vix_extreme"] = True
        elif vix_f >= VIX_ELEVATED:
            confirming += 1
            reasons.append(f"VIX={vix_f:.1f} — elevated, market stress present")
            evidence["vix_elevated"] = True

        # ── Inverted yield curve ───────────────────────────────────────────────
        spread = ctx.get("yield_curve_spread")
        if spread is not None and float(spread) < 0:
            confirming += 1
            reasons.append(f"Yield curve inverted (spread={spread:.2f}%) — recession signal")
            evidence["yield_curve_inverted"] = True

        # ── High-yield credit stress ───────────────────────────────────────────
        hy_spread = ctx.get("hy_credit_spread")
        if hy_spread is not None and float(hy_spread) > 500:
            confirming += 1
            reasons.append(f"HY OAS spread={hy_spread:.0f}bps — credit market stress")
            evidence["hy_credit_stress"] = True

        # ── Negative sentiment ────────────────────────────────────────────────
        social = ctx.get("social_score", 0.0)
        if social and float(social) < -0.3:
            confirming += 1
            reasons.append(f"Social sentiment={social:.2f} — negative news/retail sentiment")
            evidence["social_negative"] = True

        # ── Confidence calculation ─────────────────────────────────────────────
        conf = BASE_CONFIDENCE + confirming * SIGNAL_CONFIRMING_WEIGHT
        if regime_upper == "GREEN":
            conf = min(conf, 0.55)
        confidence = round(min(1.0, max(0.1, conf)), 3)

        reasoning = (
            f"Bearish case for {state.ticker} in {regime} regime. "
            + " ".join(reasons)
            + f" Confirming signals: {confirming}. Confidence: {confidence:.0%}."
        )

        return AgentArgument(
            agent=AgentRole.BEAR,
            phase=DebatePhase.ARGUING,
            position="bearish",
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
        )

    async def rebut(self, state: DebateState, challenge: CrossExamination) -> Rebuttal:
        """Bear agent defends its position against a cross-examination."""
        ctx = state.macro_context
        regime = state.regime or ctx.get("regime", "YELLOW")
        original_arg = state.get_argument_by_role(AgentRole.BEAR)
        original_conf = original_arg.confidence if original_arg else BASE_CONFIDENCE

        vulnerability = challenge.vulnerability
        severity = challenge.severity

        rebuttal_conf = round(max(0.1, original_conf - severity * 0.3), 3)

        if "insider" in vulnerability.lower():
            rebuttal_text = (
                "Insider buying can be noise — single cluster data point vs systemic macro risk. "
                "Bear case is built on regime + credit spread + VIX, not refuted by one cluster."
            )
        elif "regime" in vulnerability.lower() and regime.upper() == "GREEN":
            rebuttal_text = (
                "Acknowledging GREEN regime tailwind. However, bearish signals represent "
                "a developing reversal pattern. Regime lags price action — the current signals "
                "may be early warnings before the regime flips to YELLOW."
            )
            rebuttal_conf = round(max(0.1, original_conf - severity * 0.4), 3)
        elif "single indicator" in vulnerability.lower() or "concentration" in vulnerability.lower():
            rebuttal_text = (
                "Bear case is multi-signal: regime + VIX + credit spreads + yield curve. "
                "These are independent indicators from different asset classes."
            )
        else:
            rebuttal_text = (
                f"Challenge noted: {vulnerability}. "
                "Bear case acknowledges this uncertainty but macro headwinds are structural, "
                "not easily dismissed by short-term positive signals."
            )

        return Rebuttal(
            agent=AgentRole.BEAR,
            original_argument_id="bear",
            challenge_addressed=vulnerability,
            rebuttal_text=rebuttal_text,
            confidence_after_rebuttal=rebuttal_conf,
        )
