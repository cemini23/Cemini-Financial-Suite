"""Cemini Financial Suite — Risk Agent / Devil's Advocate (Step 47).

Phase 3 (CROSS_EXAMINING): Reads both Bull and Bear arguments from the blackboard.
Identifies the strongest argument and attacks its vulnerabilities.
Also provides a risk assessment (position sizing guidance).

Devil's Advocate logic:
  1. Target the highest-confidence argument — it carries the most risk if wrong
  2. Find contradictions between argument position and macro evidence
  3. Flag single-indicator reliance (concentration risk)
  4. Flag regime/position mismatches (bull in RED, bear in GREEN)
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
    Rebuttal,
)


class RiskAgent(BaseAgent):
    """Devil's Advocate: cross-examines both sides and provides risk assessment.

    Does NOT take a bullish or bearish position — its role is to stress-test
    the strongest arguments and surface hidden risks.
    """

    def generate_challenges(self, state: DebateState) -> list[CrossExamination]:
        """Generate cross-examination challenges targeting argument vulnerabilities.

        Called after execute() to produce the actual challenge objects.
        Returns a list of CrossExamination objects (typically 1-3).
        """
        challenges: list[CrossExamination] = []
        ctx = state.macro_context
        regime = (state.regime or ctx.get("regime", "YELLOW")).upper()

        bull_arg = state.get_argument_by_role(AgentRole.BULL)
        bear_arg = state.get_argument_by_role(AgentRole.BEAR)

        if bull_arg is None and bear_arg is None:
            return challenges

        # ── Challenge 1: Target the strongest argument ─────────────────────────
        if bull_arg and bear_arg:
            if bull_arg.confidence >= bear_arg.confidence:
                target = bull_arg
                target_role = AgentRole.BULL
            else:
                target = bear_arg
                target_role = AgentRole.BEAR
        elif bull_arg:
            target = bull_arg
            target_role = AgentRole.BULL
        else:
            target = bear_arg
            target_role = AgentRole.BEAR

        # ── Regime contradiction challenge ─────────────────────────────────────
        if target_role == AgentRole.BULL and regime == "RED":
            challenges.append(CrossExamination(
                target_agent=AgentRole.BULL,
                vulnerability="regime_contradiction",
                severity=0.75,
                challenge_question=(
                    "How do you justify a bullish position when the regime is RED — "
                    "indicating SPY below its 50-day SMA? Historically, long entries "
                    "in RED regimes have negative expected value."
                ),
            ))

        if target_role == AgentRole.BEAR and regime == "GREEN":
            challenges.append(CrossExamination(
                target_agent=AgentRole.BEAR,
                vulnerability="regime_contradiction",
                severity=0.70,
                challenge_question=(
                    "How do you justify a bearish position when the regime is GREEN — "
                    "SPY trending above its 21-day EMA? Shorting a trending market "
                    "has elevated stop-out risk."
                ),
            ))

        # ── Challenge 2: Insider data contradiction ────────────────────────────
        edgar_type = ctx.get("edgar_alert_type", "")
        if edgar_type == "insider_cluster" and target_role == AgentRole.BEAR:
            challenges.append(CrossExamination(
                target_agent=AgentRole.BEAR,
                vulnerability="insider_data_ignored",
                severity=0.60,
                challenge_question=(
                    "An insider buying cluster was detected (Step 17). Insiders have "
                    "material non-public information and are subject to legal consequences "
                    "for trading on it. Why is the bear case ignoring this signal?"
                ),
            ))

        # ── Challenge 3: Single-indicator concentration risk ───────────────────
        evidence_keys = list(target.evidence.keys())
        meaningful_keys = [k for k in evidence_keys if k not in ("regime",)]
        if len(meaningful_keys) <= 1:
            challenges.append(CrossExamination(
                target_agent=target_role,
                vulnerability="single_indicator_concentration",
                severity=0.50,
                challenge_question=(
                    f"The {target_role.value} argument relies on very few signal sources "
                    f"({len(meaningful_keys)} non-regime indicators). RSI and momentum "
                    "indicators can give false signals in choppy markets. What is the "
                    "confidence if the primary indicator turns out to be noise?"
                ),
            ))

        # ── Challenge 4: No-data challenge (both agents have no evidence) ──────
        if not challenges and bull_arg and bear_arg:
            # Generic devil's advocate challenge: what's the base rate?
            challenges.append(CrossExamination(
                target_agent=AgentRole.BULL if bull_arg.confidence >= bear_arg.confidence else AgentRole.BEAR,
                vulnerability="base_rate_neglect",
                severity=0.40,
                challenge_question=(
                    "What is the base rate for this setup? "
                    "Even with confirming signals, most breakout attempts fail. "
                    "Is the confidence calibrated to historical win rates?"
                ),
            ))

        return challenges

    async def execute(self, state: DebateState) -> AgentArgument:
        """Produce a risk assessment argument (not bullish/bearish — 'assessment')."""
        ctx = state.macro_context
        regime = (state.regime or ctx.get("regime", "YELLOW")).upper()

        bull_arg = state.get_argument_by_role(AgentRole.BULL)
        bear_arg = state.get_argument_by_role(AgentRole.BEAR)

        bull_conf = bull_arg.confidence if bull_arg else 0.0
        bear_conf = bear_arg.confidence if bear_arg else 0.0
        margin = abs(bull_conf - bear_conf)

        # Risk assessment: lower margin → higher uncertainty → more conservative sizing
        if margin < 0.1:
            risk_level = "HIGH"
            size_rec = "0.5x normal position — thesis unclear, reduce exposure"
        elif margin < 0.2:
            risk_level = "MEDIUM"
            size_rec = "0.75x normal position — mild conviction differential"
        else:
            risk_level = "LOW"
            size_rec = "1.0x normal position — clear conviction differential"

        # Regime risk note
        if regime == "RED":
            size_rec = "0.5x — RED regime hard cap on new longs"
        elif regime == "YELLOW":
            size_rec += " (YELLOW regime: no new aggressive longs)"

        challenges = self.generate_challenges(state)
        n_challenges = len(challenges)

        reasoning = (
            f"Risk assessment for {state.ticker} in {regime} regime. "
            f"Bull confidence={bull_conf:.2f}, Bear confidence={bear_conf:.2f}, "
            f"margin={margin:.2f}. Risk level: {risk_level}. "
            f"Position sizing: {size_rec}. "
            f"Generated {n_challenges} cross-examination challenge(s)."
        )

        return AgentArgument(
            agent=AgentRole.RISK,
            phase=DebatePhase.CROSS_EXAMINING,
            position="assessment",
            confidence=round(BASE_CONFIDENCE, 3),
            reasoning=reasoning,
            evidence={
                "risk_level": risk_level,
                "size_recommendation": size_rec,
                "bull_confidence": bull_conf,
                "bear_confidence": bear_conf,
                "margin": round(margin, 3),
                "challenges_generated": n_challenges,
            },
        )

    async def rebut(self, state: DebateState, challenge: CrossExamination) -> Rebuttal:
        """Risk agent itself is never directly challenged (it is the challenger)."""
        return Rebuttal(
            agent=AgentRole.RISK,
            original_argument_id="risk",
            challenge_addressed=challenge.vulnerability,
            rebuttal_text="Risk assessment stands — this agent challenges, it does not take sides.",
            confidence_after_rebuttal=BASE_CONFIDENCE,
        )
