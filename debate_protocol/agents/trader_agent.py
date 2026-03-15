"""Cemini Financial Suite — Trader Agent (Step 47).

Phase 5 (DECIDING): Reads the full debate state (arguments, cross-examinations,
rebuttals) and synthesizes a final DebateVerdict.

Deterministic scoring:
  1. Start with raw bull/bear confidence from ARGUING phase
  2. Adjust for rebuttals (maintained confidence = argument survived; dropped = weakened)
  3. Apply regime-weighted tie-breaking via tie_breaker.resolve()
  4. Include risk notes from the Risk agent
"""
from __future__ import annotations

from debate_protocol.agents.base import BaseAgent
from debate_protocol.config import BASE_CONFIDENCE
from debate_protocol.models import (
    AgentArgument,
    AgentRole,
    CrossExamination,
    DebatePhase,
    DebateState,
    DebateVerdict,
    Rebuttal,
)
from debate_protocol import tie_breaker as tb


class TraderAgent(BaseAgent):
    """Synthesizes the final verdict after all debate phases complete."""

    async def synthesize(self, state: DebateState) -> DebateVerdict:
        """Produce a DebateVerdict from the full debate state."""
        ctx = state.macro_context
        regime = state.regime or ctx.get("regime", "YELLOW")

        # ── Collect raw scores ─────────────────────────────────────────────────
        bull_arg = state.get_argument_by_role(AgentRole.BULL)
        bear_arg = state.get_argument_by_role(AgentRole.BEAR)
        risk_arg = state.get_argument_by_role(AgentRole.RISK)

        bull_score = bull_arg.confidence if bull_arg else BASE_CONFIDENCE * 0.5
        bear_score = bear_arg.confidence if bear_arg else BASE_CONFIDENCE * 0.5

        # ── Adjust for rebuttals ───────────────────────────────────────────────
        # If a rebuttal dropped confidence → the original argument was weakened
        # If it maintained/increased → the argument survived cross-examination
        for rebuttal in state.rebuttals:
            if rebuttal.agent == AgentRole.BULL:
                original_conf = bull_arg.confidence if bull_arg else BASE_CONFIDENCE
                # Blend toward rebuttal confidence (rebuttal is the updated view)
                bull_score = round((original_conf + rebuttal.confidence_after_rebuttal) / 2, 3)
            elif rebuttal.agent == AgentRole.BEAR:
                original_conf = bear_arg.confidence if bear_arg else BASE_CONFIDENCE
                bear_score = round((original_conf + rebuttal.confidence_after_rebuttal) / 2, 3)

        # ── Apply regime tie-breaking ──────────────────────────────────────────
        action, multiplier_applied, tie_break_used = tb.resolve(bull_score, bear_score, regime)

        # ── Confidence in verdict = distance between scores ────────────────────
        raw_margin = abs(bull_score - bear_score)
        verdict_confidence = round(min(1.0, 0.5 + raw_margin * 1.5), 3)

        # ── Risk notes from risk agent ─────────────────────────────────────────
        risk_notes = ""
        if risk_arg:
            risk_notes = risk_arg.evidence.get("size_recommendation", "")

        # ── Build reasoning summary ────────────────────────────────────────────
        reasoning = (
            f"Trader synthesis for {state.ticker}: "
            f"bull_score={bull_score:.3f}, bear_score={bear_score:.3f}, "
            f"regime={regime}, action={action}, "
            f"regime_multiplier={multiplier_applied}, tie_break={tie_break_used}. "
            f"Debate ran {len(state.arguments)} arguments, "
            f"{len(state.cross_examinations)} challenges, "
            f"{len(state.rebuttals)} rebuttals."
        )

        return DebateVerdict(
            action=action,
            ticker=state.ticker,
            confidence=verdict_confidence,
            bull_score=round(bull_score, 3),
            bear_score=round(bear_score, 3),
            regime=regime,
            regime_multiplier_applied=multiplier_applied,
            tie_break_used=tie_break_used,
            reasoning=reasoning,
            risk_notes=risk_notes,
        )

    async def execute(self, state: DebateState) -> AgentArgument:
        """TraderAgent does not produce an argument — it synthesizes a verdict.

        This method is included to satisfy the BaseAgent ABC. Returns a
        neutral argument summarising the synthesis.
        """
        verdict = await self.synthesize(state)
        return AgentArgument(
            agent=AgentRole.TRADER,
            phase=DebatePhase.DECIDING,
            position="neutral",
            confidence=verdict.confidence,
            reasoning=verdict.reasoning,
            evidence={"action": verdict.action, "bull_score": verdict.bull_score, "bear_score": verdict.bear_score},
        )

    async def rebut(self, state: DebateState, challenge: CrossExamination) -> Rebuttal:
        """Trader is never challenged — it decides, not argues."""
        return Rebuttal(
            agent=AgentRole.TRADER,
            original_argument_id="trader",
            challenge_addressed=challenge.vulnerability,
            rebuttal_text="Trader synthesizes — it does not defend a position.",
            confidence_after_rebuttal=BASE_CONFIDENCE,
        )
