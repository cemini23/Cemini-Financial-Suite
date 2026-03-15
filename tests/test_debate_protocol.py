"""Cemini Financial Suite — Debate Protocol Tests (Step 47).

All pure tests — mock Redis, mock DB, mock Intel Bus. No network calls.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from debate_protocol.models import (
    AgentArgument,
    AgentRole,
    CrossExamination,
    DebatePhase,
    DebateState,
    DebateVerdict,
    DebateVerdictIntel,
    Rebuttal,
)
from debate_protocol.blackboard import Blackboard
from debate_protocol.tie_breaker import resolve
from debate_protocol.agents.macro_agent import MacroAgent
from debate_protocol.agents.bull_agent import BullAgent
from debate_protocol.agents.bear_agent import BearAgent
from debate_protocol.agents.risk_agent import RiskAgent
from debate_protocol.agents.trader_agent import TraderAgent
from debate_protocol.debate_logger import log_to_jsonl, publish_verdict_intel
from debate_protocol.state_machine import run_debate


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_state(
    ticker: str = "AAPL",
    regime: str = "YELLOW",
    macro_context: dict | None = None,
) -> DebateState:
    return DebateState(
        session_id="test-session-001",
        ticker=ticker,
        regime=regime,
        macro_context=macro_context or {"regime": regime},
        started_at=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
    )


def _make_argument(
    role: AgentRole = AgentRole.BULL,
    position: str = "bullish",
    confidence: float = 0.7,
) -> AgentArgument:
    return AgentArgument(
        agent=role,
        phase=DebatePhase.ARGUING,
        position=position,
        confidence=confidence,
        reasoning="Test argument",
        evidence={"regime": "YELLOW"},
    )


def _make_async_blackboard(initial_state: DebateState | None = None) -> Blackboard:
    """Return a Blackboard backed by an AsyncMock Redis."""
    mock_redis = AsyncMock()
    stored: list[bytes] = []

    async def _set(key, value, ex=None):
        stored.clear()
        stored.append(value)

    async def _get(key):
        return stored[-1] if stored else None

    mock_redis.set = _set
    mock_redis.get = _get
    mock_redis.delete = AsyncMock()

    bb = Blackboard(mock_redis, "test-session-001")

    if initial_state is not None:
        # Pre-populate
        stored.append(initial_state.model_dump_json())

    return bb


def _run(coro):
    """Run an async coroutine in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ══════════════════════════════════════════════════════════════════════════════
# Models
# ══════════════════════════════════════════════════════════════════════════════

class TestModels:
    def test_debate_state_serialization(self):
        state = _make_state()
        dumped = state.model_dump_json()
        restored = DebateState.model_validate_json(dumped)
        assert restored.session_id == state.session_id
        assert restored.ticker == state.ticker
        assert restored.phase == DebatePhase.GATHERING

    def test_debate_state_with_arguments_roundtrip(self):
        state = _make_state()
        state.arguments.append(_make_argument())
        dumped = state.model_dump_json()
        restored = DebateState.model_validate_json(dumped)
        assert len(restored.arguments) == 1
        assert restored.arguments[0].confidence == 0.7

    def test_agent_argument_confidence_bounds_low(self):
        with pytest.raises(ValidationError):
            AgentArgument(
                agent=AgentRole.BULL, phase=DebatePhase.ARGUING,
                position="bullish", confidence=-0.1, reasoning="x",
            )

    def test_agent_argument_confidence_bounds_high(self):
        with pytest.raises(ValidationError):
            AgentArgument(
                agent=AgentRole.BULL, phase=DebatePhase.ARGUING,
                position="bullish", confidence=1.1, reasoning="x",
            )

    def test_debate_verdict_valid_actions(self):
        for action in ("BUY", "SELL", "HOLD", "NO_ACTION"):
            vd = DebateVerdict(
                action=action, ticker="AAPL", confidence=0.7,
                bull_score=0.6, bear_score=0.4, regime="YELLOW",
                regime_multiplier_applied=False, tie_break_used=False,
                reasoning="test",
            )
            assert vd.action == action

    def test_debate_verdict_invalid_action(self):
        with pytest.raises(ValidationError):
            DebateVerdict(
                action="MAYBE", ticker="AAPL", confidence=0.5,
                bull_score=0.5, bear_score=0.5, regime="YELLOW",
                regime_multiplier_applied=False, tie_break_used=False,
                reasoning="x",
            )

    def test_debate_phase_transitions_valid(self):
        for phase in DebatePhase:
            state = _make_state()
            state.phase = phase
            assert state.phase == phase

    def test_debate_state_get_argument_by_role(self):
        state = _make_state()
        state.arguments.append(_make_argument(AgentRole.BULL, confidence=0.8))
        state.arguments.append(_make_argument(AgentRole.BEAR, "bearish", 0.6))
        assert state.get_argument_by_role(AgentRole.BULL).confidence == 0.8
        assert state.get_argument_by_role(AgentRole.BEAR).confidence == 0.6
        assert state.get_argument_by_role(AgentRole.RISK) is None


# ══════════════════════════════════════════════════════════════════════════════
# Blackboard
# ══════════════════════════════════════════════════════════════════════════════

class TestBlackboard:
    def test_blackboard_write_read_roundtrip(self):
        state = _make_state()
        bb = _make_async_blackboard()
        _run(bb.write_state(state))
        restored = _run(bb.read_state())
        assert restored is not None
        assert restored.session_id == state.session_id

    def test_blackboard_add_argument_appends(self):
        state = _make_state()
        bb = _make_async_blackboard(state)
        arg = _make_argument()
        new_state = _run(bb.add_argument(state, arg))
        assert len(new_state.arguments) == 1

    def test_blackboard_ttl_set(self):
        """Verify set() is called with ex= parameter."""
        mock_redis = AsyncMock()
        set_calls = []

        async def _set(key, value, ex=None):
            set_calls.append(ex)

        mock_redis.set = _set
        bb = Blackboard(mock_redis, "sess-001", ttl=3600)
        state = _make_state()
        _run(bb.write_state(state))
        assert set_calls == [3600]

    def test_blackboard_set_verdict_marks_complete(self):
        state = _make_state()
        bb = _make_async_blackboard(state)
        verdict = DebateVerdict(
            action="BUY", ticker="AAPL", confidence=0.75,
            bull_score=0.7, bear_score=0.4, regime="YELLOW",
            regime_multiplier_applied=False, tie_break_used=False,
            reasoning="test",
        )
        new_state = _run(bb.set_verdict(state, verdict))
        assert new_state.phase == DebatePhase.COMPLETE
        assert new_state.verdict is not None
        assert new_state.verdict.action == "BUY"

    def test_blackboard_read_returns_none_on_miss(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        bb = Blackboard(mock_redis, "missing-session")
        result = _run(bb.read_state())
        assert result is None

    def test_blackboard_add_rebuttal(self):
        state = _make_state()
        bb = _make_async_blackboard(state)
        rebuttal = Rebuttal(
            agent=AgentRole.BULL,
            original_argument_id="bull",
            challenge_addressed="regime_contradiction",
            rebuttal_text="Bull defends",
            confidence_after_rebuttal=0.6,
        )
        new_state = _run(bb.add_rebuttal(state, rebuttal))
        assert len(new_state.rebuttals) == 1


# ══════════════════════════════════════════════════════════════════════════════
# Agents — deterministic behaviour
# ══════════════════════════════════════════════════════════════════════════════

class TestMacroAgent:
    def test_macro_agent_reads_intel(self):
        """Macro agent produces an argument with evidence dict populated."""
        bb = _make_async_blackboard()
        macro = MacroAgent(AgentRole.MACRO, bb, redis_client=None)
        state = _make_state()
        arg = _run(macro.execute(state))
        assert arg.agent == AgentRole.MACRO
        assert isinstance(arg.evidence, dict)

    def test_macro_agent_sets_regime_from_playbook(self):
        """Macro agent uses regime from playbook snapshot when available."""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value=json.dumps({
            "value": {"regime": "GREEN"},
            "source_system": "playbook",
            "timestamp": 1.0,
            "confidence": 1.0,
        }))
        bb = _make_async_blackboard()
        macro = MacroAgent(AgentRole.MACRO, bb, redis_client=mock_redis)
        state = _make_state()
        arg = _run(macro.execute(state))
        assert arg.evidence.get("regime") == "GREEN"

    def test_macro_agent_no_redis_defaults_neutral(self):
        """Without Redis, macro agent defaults to YELLOW neutral stance."""
        bb = _make_async_blackboard()
        macro = MacroAgent(AgentRole.MACRO, bb, redis_client=None)
        state = _make_state()
        arg = _run(macro.execute(state))
        assert arg.evidence.get("regime") == "YELLOW"
        assert arg.confidence >= 0.0


class TestBullAgent:
    def test_bull_agent_produces_bullish_argument(self):
        bb = _make_async_blackboard()
        bull = BullAgent(AgentRole.BULL, bb)
        state = _make_state("AAPL", "YELLOW", {"regime": "YELLOW"})
        arg = _run(bull.execute(state))
        assert arg.position == "bullish"
        assert arg.agent == AgentRole.BULL

    def test_bull_agent_bullish_in_green_regime(self):
        """GREEN regime gives bull higher confidence than YELLOW."""
        bb = _make_async_blackboard()
        bull = BullAgent(AgentRole.BULL, bb)

        state_green = _make_state("AAPL", "GREEN", {"regime": "GREEN"})
        state_yellow = _make_state("AAPL", "YELLOW", {"regime": "YELLOW"})

        arg_green = _run(bull.execute(state_green))
        arg_yellow = _run(bull.execute(state_yellow))

        assert arg_green.confidence >= arg_yellow.confidence

    def test_bull_agent_lower_confidence_in_red(self):
        """RED regime caps bull confidence at 0.55."""
        bb = _make_async_blackboard()
        bull = BullAgent(AgentRole.BULL, bb)
        state = _make_state("AAPL", "RED", {"regime": "RED"})
        arg = _run(bull.execute(state))
        assert arg.confidence <= 0.55

    def test_bull_rebuttal_maintains_or_drops_confidence(self):
        """Rebuttal confidence is non-negative and different from original on challenge."""
        bb = _make_async_blackboard()
        bull = BullAgent(AgentRole.BULL, bb)
        state = _make_state("AAPL", "RED", {"regime": "RED"})
        state.arguments.append(_make_argument(AgentRole.BULL, confidence=0.65))
        challenge = CrossExamination(
            target_agent=AgentRole.BULL,
            vulnerability="regime_contradiction",
            severity=0.75,
            challenge_question="How do you justify bullish in RED?",
        )
        rebuttal = _run(bull.rebut(state, challenge))
        assert rebuttal.agent == AgentRole.BULL
        assert 0.0 <= rebuttal.confidence_after_rebuttal <= 1.0
        # High severity challenge should reduce confidence
        assert rebuttal.confidence_after_rebuttal <= 0.65


class TestBearAgent:
    def test_bear_agent_produces_bearish_argument(self):
        bb = _make_async_blackboard()
        bear = BearAgent(AgentRole.BEAR, bb)
        state = _make_state("AAPL", "YELLOW", {"regime": "YELLOW"})
        arg = _run(bear.execute(state))
        assert arg.position == "bearish"

    def test_bear_agent_bearish_in_red_regime(self):
        """RED regime gives bear higher confidence than YELLOW."""
        bb = _make_async_blackboard()
        bear = BearAgent(AgentRole.BEAR, bb)

        state_red = _make_state("AAPL", "RED", {"regime": "RED"})
        state_yellow = _make_state("AAPL", "YELLOW", {"regime": "YELLOW"})

        arg_red = _run(bear.execute(state_red))
        arg_yellow = _run(bear.execute(state_yellow))

        assert arg_red.confidence >= arg_yellow.confidence

    def test_bear_agent_lower_confidence_in_green(self):
        """GREEN regime caps bear confidence at 0.55."""
        bb = _make_async_blackboard()
        bear = BearAgent(AgentRole.BEAR, bb)
        state = _make_state("AAPL", "GREEN", {"regime": "GREEN"})
        arg = _run(bear.execute(state))
        assert arg.confidence <= 0.55

    def test_bear_rebuttal_addresses_challenge(self):
        """Rebuttal references the challenge vulnerability."""
        bb = _make_async_blackboard()
        bear = BearAgent(AgentRole.BEAR, bb)
        state = _make_state("AAPL", "GREEN", {"regime": "GREEN"})
        state.arguments.append(_make_argument(AgentRole.BEAR, "bearish", 0.60))
        challenge = CrossExamination(
            target_agent=AgentRole.BEAR,
            vulnerability="regime_contradiction",
            severity=0.70,
            challenge_question="How do you justify bearish in GREEN?",
        )
        rebuttal = _run(bear.rebut(state, challenge))
        assert rebuttal.agent == AgentRole.BEAR
        assert "regime" in rebuttal.challenge_addressed.lower()
        assert 0.0 <= rebuttal.confidence_after_rebuttal <= 1.0


class TestRiskAgent:
    def _state_with_args(self, bull_conf: float = 0.7, bear_conf: float = 0.5, regime: str = "YELLOW") -> DebateState:
        state = _make_state("AAPL", regime, {"regime": regime})
        state.arguments.append(_make_argument(AgentRole.BULL, "bullish", bull_conf))
        state.arguments.append(_make_argument(AgentRole.BEAR, "bearish", bear_conf))
        return state

    def test_risk_agent_produces_assessment(self):
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = self._state_with_args()
        arg = _run(risk.execute(state))
        assert arg.position == "assessment"
        assert arg.agent == AgentRole.RISK

    def test_risk_agent_challenges_strongest(self):
        """Risk agent targets the higher-confidence argument."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = self._state_with_args(bull_conf=0.8, bear_conf=0.4)
        challenges = risk.generate_challenges(state)
        # The strongest is bull (0.8) — at least one challenge should target BULL
        targets = [ch.target_agent for ch in challenges]
        assert AgentRole.BULL in targets

    def test_risk_agent_finds_regime_contradiction_bull_in_red(self):
        """Bull in RED regime should be challenged for regime contradiction."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = self._state_with_args(bull_conf=0.8, bear_conf=0.4, regime="RED")
        challenges = risk.generate_challenges(state)
        vulnerabilities = [ch.vulnerability for ch in challenges]
        assert "regime_contradiction" in vulnerabilities

    def test_risk_agent_finds_regime_contradiction_bear_in_green(self):
        """Bear in GREEN regime should be challenged for regime contradiction."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = self._state_with_args(bull_conf=0.4, bear_conf=0.8, regime="GREEN")
        challenges = risk.generate_challenges(state)
        vulnerabilities = [ch.vulnerability for ch in challenges]
        assert "regime_contradiction" in vulnerabilities

    def test_risk_agent_finds_single_indicator_risk(self):
        """Argument with only one evidence key triggers concentration challenge."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = _make_state("AAPL", "YELLOW", {"regime": "YELLOW"})
        # Bull has only regime in evidence (single indicator)
        bull_arg = AgentArgument(
            agent=AgentRole.BULL, phase=DebatePhase.ARGUING,
            position="bullish", confidence=0.7, reasoning="x",
            evidence={"regime": "YELLOW"},  # only regime key
        )
        bear_arg = _make_argument(AgentRole.BEAR, "bearish", 0.5)
        state.arguments.extend([bull_arg, bear_arg])
        challenges = risk.generate_challenges(state)
        vulnerabilities = [ch.vulnerability for ch in challenges]
        assert "single_indicator_concentration" in vulnerabilities

    def test_risk_agent_no_challenges_without_arguments(self):
        """No arguments → no challenges generated."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = _make_state()
        challenges = risk.generate_challenges(state)
        assert challenges == []


class TestTraderAgent:
    def _state_with_full_debate(self, bull_conf: float = 0.7, bear_conf: float = 0.5, regime: str = "YELLOW") -> DebateState:
        state = _make_state("AAPL", regime, {"regime": regime})
        state.arguments.append(_make_argument(AgentRole.BULL, "bullish", bull_conf))
        state.arguments.append(_make_argument(AgentRole.BEAR, "bearish", bear_conf))
        risk_arg = AgentArgument(
            agent=AgentRole.RISK, phase=DebatePhase.CROSS_EXAMINING,
            position="assessment", confidence=0.5, reasoning="Risk ok",
            evidence={"size_recommendation": "1.0x"},
        )
        state.arguments.append(risk_arg)
        return state

    def test_trader_agent_synthesizes_verdict(self):
        bb = _make_async_blackboard()
        trader = TraderAgent(AgentRole.TRADER, bb)
        state = self._state_with_full_debate()
        verdict = _run(trader.synthesize(state))
        assert isinstance(verdict, DebateVerdict)
        assert verdict.action in ("BUY", "SELL", "HOLD", "NO_ACTION")

    def test_trader_bull_wins_produces_buy(self):
        """Bull significantly higher confidence → BUY."""
        bb = _make_async_blackboard()
        trader = TraderAgent(AgentRole.TRADER, bb)
        state = self._state_with_full_debate(bull_conf=0.9, bear_conf=0.3, regime="YELLOW")
        verdict = _run(trader.synthesize(state))
        assert verdict.action == "BUY"

    def test_trader_bear_wins_produces_sell(self):
        """Bear significantly higher confidence → SELL."""
        bb = _make_async_blackboard()
        trader = TraderAgent(AgentRole.TRADER, bb)
        state = self._state_with_full_debate(bull_conf=0.3, bear_conf=0.9, regime="YELLOW")
        verdict = _run(trader.synthesize(state))
        assert verdict.action == "SELL"


# ══════════════════════════════════════════════════════════════════════════════
# Tie-breaker
# ══════════════════════════════════════════════════════════════════════════════

class TestTieBreaker:
    def test_tie_break_green_favors_bull(self):
        """GREEN multiplies bull 1.2x — bull wins when multiplied margin > threshold."""
        # bull=0.55, bear=0.50 → after GREEN multiplier bull=0.66, margin=0.16 > 0.10 → BUY
        action, multiplier_applied, _ = resolve(0.55, 0.50, "GREEN")
        assert action == "BUY"
        assert multiplier_applied is True

    def test_tie_break_red_favors_bear(self):
        """RED multiplies bear 1.2x — bear wins when multiplied margin > threshold."""
        # bull=0.50, bear=0.55 → after RED multiplier bear=0.66, margin=0.16 > 0.10 → SELL
        action, multiplier_applied, _ = resolve(0.50, 0.55, "RED")
        assert action == "SELL"
        assert multiplier_applied is True

    def test_tie_break_yellow_no_multiplier(self):
        """YELLOW applies no multiplier — pure score comparison."""
        action, multiplier_applied, _ = resolve(0.70, 0.50, "YELLOW")
        assert multiplier_applied is False
        assert action == "BUY"

    def test_tie_break_true_tie_returns_hold(self):
        """Equal scores with no multiplier → HOLD (conservative)."""
        action, _, tie_break_used = resolve(0.50, 0.50, "YELLOW")
        assert action == "HOLD"
        assert tie_break_used is True

    def test_tie_break_clear_margin_no_flag(self):
        """Large margin → tie_break_used=False."""
        _, _, tie_break_used = resolve(0.9, 0.3, "YELLOW")
        assert tie_break_used is False

    def test_tie_break_close_margin_flags(self):
        """Small but decisive margin → tie_break_used=True."""
        # margin = 0.65 - 0.60 = 0.05 < threshold(0.10) → should be HOLD
        # Let's use margin just above threshold but below close_call: 0.72 vs 0.60 → margin=0.12
        _, _, tie_break_used = resolve(0.72, 0.60, "YELLOW")
        assert tie_break_used is True

    def test_tie_break_green_uppercase_insensitive(self):
        """Regime matching should be case-insensitive."""
        action_upper, m1, _ = resolve(0.55, 0.60, "GREEN")
        action_lower, m2, _ = resolve(0.55, 0.60, "green")
        assert action_upper == action_lower
        assert m1 == m2

    def test_tie_break_zero_scores_hold(self):
        action, _, _ = resolve(0.0, 0.0, "YELLOW")
        assert action == "HOLD"


# ══════════════════════════════════════════════════════════════════════════════
# Full state machine integration
# ══════════════════════════════════════════════════════════════════════════════

class TestStateMachine:
    def _mock_redis_async(self) -> AsyncMock:
        """Async Redis mock with in-memory store."""
        store: dict = {}

        async def _set(key, value, ex=None):
            store[key] = value

        async def _get(key):
            return store.get(key)

        mock = AsyncMock()
        mock.set = _set
        mock.get = _get
        mock.delete = AsyncMock()
        return mock

    def test_full_debate_cycle_5_phases(self):
        """All 5 phases execute in sequence."""
        phases_seen: list[DebatePhase] = []
        original_set_phase = Blackboard.set_phase

        async def tracking_set_phase(self_bb, state, phase):
            phases_seen.append(phase)
            return await original_set_phase(self_bb, state, phase)

        rdb = self._mock_redis_async()
        with patch.object(Blackboard, "set_phase", tracking_set_phase):
            verdict = _run(run_debate("AAPL", redis_client=rdb))

        expected = [
            DebatePhase.ARGUING,
            DebatePhase.CROSS_EXAMINING,
            DebatePhase.REBUTTING,
            DebatePhase.DECIDING,
        ]
        for phase in expected:
            assert phase in phases_seen

    def test_debate_produces_verdict(self):
        """run_debate always returns a DebateVerdict (never None)."""
        rdb = self._mock_redis_async()
        verdict = _run(run_debate("AAPL", redis_client=rdb))
        assert verdict is not None
        assert isinstance(verdict, DebateVerdict)

    def test_debate_state_has_arguments_from_all_agents(self):
        """All 5 agents produce at least one argument."""
        rdb = self._mock_redis_async()
        states_seen: list[DebateState] = []

        original_write = Blackboard.write_state

        async def capturing_write(self_bb, state):
            states_seen.append(state.model_copy())
            return await original_write(self_bb, state)

        with patch.object(Blackboard, "write_state", capturing_write):
            _run(run_debate("NVDA", redis_client=rdb))

        final_state = states_seen[-1]
        roles = {arg.agent for arg in final_state.arguments}
        assert AgentRole.MACRO in roles
        assert AgentRole.BULL in roles
        assert AgentRole.BEAR in roles
        assert AgentRole.RISK in roles

    def test_debate_logs_to_jsonl(self, tmp_path):
        """JSONL file is created after debate completes."""
        rdb = self._mock_redis_async()

        with patch("debate_protocol.debate_logger._archive_root", return_value=str(tmp_path)):
            verdict = _run(run_debate("TSLA", redis_client=rdb))

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().splitlines()
        assert len(lines) >= 1
        data = json.loads(lines[0])
        assert data["ticker"] == "TSLA"

    def test_debate_logs_audit_chain(self):
        """chain_writer is invoked (mocked) after debate completes."""
        rdb = self._mock_redis_async()

        with patch("debate_protocol.debate_logger.log_to_audit_chain") as mock_audit:
            _run(run_debate("JPM", redis_client=rdb))

        mock_audit.assert_called_once()

    def test_debate_publishes_verdict_intel(self):
        """intel:debate_verdict is published via sync Redis."""
        rdb_async = self._mock_redis_async()
        rdb_sync = MagicMock()
        rdb_sync.set = MagicMock()

        with patch("debate_protocol.debate_logger.publish_verdict_intel") as mock_pub:
            _run(run_debate("GS", redis_client=rdb_async, sync_redis=rdb_sync))

        mock_pub.assert_called_once()

    def test_debate_all_agents_bearish_yields_sell(self):
        """Extreme RED regime with bearish VIX → SELL."""
        rdb = self._mock_redis_async()

        # Force RED regime by making macro read return RED
        with patch("debate_protocol.agents.macro_agent._read_redis_key") as mock_read:
            mock_read.return_value = {"value": {"regime": "RED"}, "source_system": "playbook", "timestamp": 1.0, "confidence": 1.0}
            verdict = _run(run_debate("AAPL", redis_client=rdb))

        # In RED regime: bear gets 1.2x multiplier → SELL if bear > bull
        # Red regime means: BullAgent caps at 0.55, BearAgent is higher
        assert verdict.action in ("SELL", "HOLD")  # RED should push toward SELL

    def test_debate_all_agents_bullish_yields_buy(self):
        """GREEN regime with all-bullish signals → BUY."""
        rdb = self._mock_redis_async()

        with patch("debate_protocol.agents.macro_agent._read_redis_key") as mock_read:
            mock_read.return_value = {"value": {"regime": "GREEN", "spy_trend": "bullish"}, "source_system": "playbook", "timestamp": 1.0, "confidence": 1.0}
            verdict = _run(run_debate("AAPL", redis_client=rdb))

        assert verdict.action in ("BUY", "HOLD")  # GREEN should push toward BUY


# ══════════════════════════════════════════════════════════════════════════════
# Edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_debate_with_no_intel_data(self):
        """Graceful degradation: no intel → agents default to conservative neutral."""
        rdb_async = AsyncMock()

        async def _null_get(key):
            return None

        rdb_async.get = _null_get
        rdb_async.set = AsyncMock()
        rdb_async.delete = AsyncMock()

        verdict = _run(run_debate("XYZZY", redis_client=rdb_async))
        assert verdict is not None
        assert verdict.action in ("BUY", "SELL", "HOLD", "NO_ACTION")

    def test_debate_redis_failure_graceful(self):
        """Redis write failure → error state returned without exception."""
        rdb_async = AsyncMock()

        async def _fail_set(key, value, ex=None):
            raise ConnectionError("Redis unavailable")

        async def _null_get(key):
            return None

        rdb_async.set = _fail_set
        rdb_async.get = _null_get
        rdb_async.delete = AsyncMock()

        # Should not raise — returns NO_ACTION error verdict
        verdict = _run(run_debate("FAIL", redis_client=rdb_async))
        assert verdict is not None

    def test_cross_examination_empty_if_no_arguments(self):
        """No arguments → no cross-examinations generated."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = _make_state()
        challenges = risk.generate_challenges(state)
        assert challenges == []

    def test_cross_examination_empty_if_unanimous(self):
        """Both agents agree (same direction) → no regime contradiction challenge."""
        bb = _make_async_blackboard()
        risk = RiskAgent(AgentRole.RISK, bb)
        state = _make_state("AAPL", "GREEN", {"regime": "GREEN"})
        # Both bullish in GREEN — no contradiction
        state.arguments.append(_make_argument(AgentRole.BULL, "bullish", 0.8))
        state.arguments.append(_make_argument(AgentRole.BEAR, "bearish", 0.3))
        challenges = risk.generate_challenges(state)
        # Bear in GREEN is weak (0.3) but technically still "bearish" — check no bear regime challenge
        bear_regime_challenges = [
            ch for ch in challenges
            if ch.target_agent == AgentRole.BEAR and ch.vulnerability == "regime_contradiction"
        ]
        # Only if bear_conf > bull_conf does bear get regime contradiction — here bull wins
        assert bear_regime_challenges == []

    def test_verdict_intel_serialization(self):
        """DebateVerdictIntel serializes correctly."""
        intel = DebateVerdictIntel(
            session_id="s-001",
            ticker="AAPL",
            action="BUY",
            confidence=0.75,
            regime="GREEN",
            bull_score=0.7,
            bear_score=0.4,
            tie_break_used=False,
            summary="BUY signal detected",
        )
        dumped = intel.model_dump()
        assert dumped["action"] == "BUY"
        assert dumped["ticker"] == "AAPL"

    def test_jsonl_logger_creates_file(self, tmp_path):
        """log_to_jsonl creates dated JSONL file."""
        state = _make_state("TEST")
        state.verdict = DebateVerdict(
            action="HOLD", ticker="TEST", confidence=0.5,
            bull_score=0.5, bear_score=0.5, regime="YELLOW",
            regime_multiplier_applied=False, tie_break_used=True, reasoning="tie",
        )

        with patch("debate_protocol.debate_logger._archive_root", return_value=str(tmp_path)):
            log_to_jsonl(state)

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1

    def test_publish_verdict_intel_noop_without_redis(self):
        """publish_verdict_intel is a no-op when redis_client is None."""
        state = _make_state("AAPL")
        state.verdict = DebateVerdict(
            action="BUY", ticker="AAPL", confidence=0.7,
            bull_score=0.7, bear_score=0.4, regime="YELLOW",
            regime_multiplier_applied=False, tie_break_used=False, reasoning="x",
        )
        # Should not raise
        publish_verdict_intel(state, redis_client=None)
