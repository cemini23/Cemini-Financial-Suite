"""
Tests for the dynamic regime confidence threshold gate.

All tests are pure (no network, no Redis, no Postgres).
The _regime_gate() function is a pure function — tested directly without
mocking any I/O.

Test coverage:
  - Threshold table sanity (BUY rises with severity, SELL/SHORT falls)
  - GREEN / YELLOW / RED thresholds for BUY
  - GREEN / YELLOW / RED thresholds for SELL
  - SHORT treated same as SELL
  - Catalyst bonus (+0.10) for EpisodicPivot / InsideBar212 in YELLOW and RED
  - Bonus NOT applied in GREEN
  - Bonus NOT applied to trend-continuation patterns (MomentumBurst etc.)
  - None / unknown regime defaults to GREEN (permissive fallback)
  - Reason string content when blocked
  - Empty reason when signal passes
  - Boundary: confidence exactly at threshold passes (not blocked)
"""

import pytest

from agents.regime_gate import (
    CATALYST_BONUS,
    CATALYST_PATTERNS,
    REGIME_THRESHOLDS,
    _regime_gate,
)


# ============================================================================
# Threshold table sanity
# ============================================================================
class TestRegimeThresholds:
    def test_all_regimes_present(self):
        for regime in ("GREEN", "YELLOW", "RED"):
            assert regime in REGIME_THRESHOLDS, f"{regime} missing from REGIME_THRESHOLDS"

    def test_all_regimes_have_buy_sell_short(self):
        for regime, thresholds in REGIME_THRESHOLDS.items():
            for action in ("BUY", "SELL", "SHORT"):
                assert action in thresholds, f"{action} missing in {regime}"

    def test_buy_threshold_increases_with_severity(self):
        """Stricter BUY requirement in worse regimes."""
        assert (
            REGIME_THRESHOLDS["GREEN"]["BUY"]
            < REGIME_THRESHOLDS["YELLOW"]["BUY"]
            < REGIME_THRESHOLDS["RED"]["BUY"]
        )

    def test_sell_threshold_decreases_with_severity(self):
        """Easier to exit/short in worse regimes."""
        assert (
            REGIME_THRESHOLDS["GREEN"]["SELL"]
            > REGIME_THRESHOLDS["YELLOW"]["SELL"]
            > REGIME_THRESHOLDS["RED"]["SELL"]
        )

    def test_short_matches_sell_in_all_regimes(self):
        for regime in ("GREEN", "YELLOW", "RED"):
            assert (
                REGIME_THRESHOLDS[regime]["SHORT"] == REGIME_THRESHOLDS[regime]["SELL"]
            ), f"SHORT != SELL threshold in {regime}"

    def test_catalyst_patterns_are_correct(self):
        assert "EpisodicPivot" in CATALYST_PATTERNS
        assert "InsideBar212" in CATALYST_PATTERNS
        # Trend-continuation patterns must NOT be in the set
        for pat in ("MomentumBurst", "ElephantBar", "VCP", "HighTightFlag"):
            assert pat not in CATALYST_PATTERNS, f"{pat} should not be a catalyst"

    def test_catalyst_bonus_is_positive(self):
        assert CATALYST_BONUS > 0


# ============================================================================
# GREEN regime
# ============================================================================
class TestGreenRegime:
    def test_buy_passes_above_threshold(self):
        blocked, _, _ = _regime_gate("BUY", 0.60, "GREEN")
        assert not blocked

    def test_buy_passes_exactly_at_threshold(self):
        """Boundary: confidence == threshold → should pass (not blocked)."""
        threshold = REGIME_THRESHOLDS["GREEN"]["BUY"]
        blocked, _, _ = _regime_gate("BUY", threshold, "GREEN")
        assert not blocked

    def test_buy_blocks_below_threshold(self):
        blocked, _, reason = _regime_gate("BUY", 0.50, "GREEN")
        assert blocked
        assert "0.55" in reason

    def test_sell_passes_above_threshold(self):
        blocked, _, _ = _regime_gate("SELL", 0.60, "GREEN")
        assert not blocked

    def test_sell_blocks_below_threshold(self):
        blocked, _, _ = _regime_gate("SELL", 0.50, "GREEN")
        assert blocked


# ============================================================================
# YELLOW regime
# ============================================================================
class TestYellowRegime:
    def test_buy_blocks_moderate_confidence(self):
        """0.60 < 0.75 → blocked in YELLOW."""
        blocked, _, _ = _regime_gate("BUY", 0.60, "YELLOW")
        assert blocked

    def test_buy_passes_high_confidence(self):
        blocked, _, _ = _regime_gate("BUY", 0.80, "YELLOW")
        assert not blocked

    def test_buy_passes_exactly_at_threshold(self):
        threshold = REGIME_THRESHOLDS["YELLOW"]["BUY"]
        blocked, _, _ = _regime_gate("BUY", threshold, "YELLOW")
        assert not blocked

    def test_sell_passes_at_lower_threshold(self):
        """SELL threshold drops to 0.50 in YELLOW — slightly easier to exit."""
        blocked, _, _ = _regime_gate("SELL", 0.50, "YELLOW")
        assert not blocked

    def test_sell_blocks_below_threshold(self):
        blocked, _, _ = _regime_gate("SELL", 0.49, "YELLOW")
        assert blocked


# ============================================================================
# RED regime
# ============================================================================
class TestRedRegime:
    def test_buy_blocks_moderate_confidence(self):
        """0.60 < 0.85 → blocked in RED."""
        blocked, _, _ = _regime_gate("BUY", 0.60, "RED")
        assert blocked

    def test_buy_passes_high_confidence(self):
        """0.90 >= 0.85 → passes in RED."""
        blocked, _, _ = _regime_gate("BUY", 0.90, "RED")
        assert not blocked

    def test_buy_passes_exactly_at_threshold(self):
        threshold = REGIME_THRESHOLDS["RED"]["BUY"]
        blocked, _, _ = _regime_gate("BUY", threshold, "RED")
        assert not blocked

    def test_sell_passes_at_low_threshold(self):
        """SELL threshold drops to 0.45 in RED — very easy to exit."""
        blocked, _, _ = _regime_gate("SELL", 0.45, "RED")
        assert not blocked

    def test_sell_passes_exactly_at_threshold(self):
        threshold = REGIME_THRESHOLDS["RED"]["SELL"]
        blocked, _, _ = _regime_gate("SELL", threshold, "RED")
        assert not blocked

    def test_sell_blocks_below_threshold(self):
        blocked, _, _ = _regime_gate("SELL", 0.40, "RED")
        assert blocked


# ============================================================================
# SHORT action
# ============================================================================
class TestShortAction:
    def test_short_same_threshold_as_sell_in_red(self):
        """SHORT uses the SELL threshold in every regime."""
        blocked_sell, _, _ = _regime_gate("SELL", 0.45, "RED")
        blocked_short, _, _ = _regime_gate("SHORT", 0.45, "RED")
        assert blocked_sell == blocked_short

    def test_short_passes_at_sell_threshold_yellow(self):
        blocked, _, _ = _regime_gate("SHORT", 0.50, "YELLOW")
        assert not blocked

    def test_short_blocks_below_sell_threshold_yellow(self):
        blocked, _, _ = _regime_gate("SHORT", 0.49, "YELLOW")
        assert blocked


# ============================================================================
# Catalyst bonus (EpisodicPivot / InsideBar212)
# ============================================================================
class TestCatalystBonus:
    def test_episodic_pivot_bonus_in_red_causes_pass(self):
        """0.78 + 0.10 bonus = 0.88 >= 0.85 → passes in RED."""
        blocked, eff, _ = _regime_gate("BUY", 0.78, "RED", signal_type="EpisodicPivot")
        assert not blocked
        assert eff == pytest.approx(0.88, abs=1e-9)

    def test_inside_bar_bonus_in_red_causes_pass(self):
        """InsideBar212 also gets the +0.10 catalyst bonus."""
        blocked, eff, _ = _regime_gate("BUY", 0.78, "RED", signal_type="InsideBar212")
        assert not blocked
        assert eff == pytest.approx(0.88, abs=1e-9)

    def test_episodic_pivot_bonus_insufficient(self):
        """0.74 + 0.10 = 0.84 < 0.85 → still blocked in RED."""
        blocked, eff, _ = _regime_gate("BUY", 0.74, "RED", signal_type="EpisodicPivot")
        assert blocked
        assert eff == pytest.approx(0.84, abs=1e-9)

    def test_episodic_pivot_bonus_in_yellow_causes_pass(self):
        """Bonus applies in YELLOW too: 0.68 + 0.10 = 0.78 >= 0.75."""
        blocked, eff, _ = _regime_gate("BUY", 0.68, "YELLOW", signal_type="EpisodicPivot")
        assert not blocked
        assert eff == pytest.approx(0.78, abs=1e-9)

    def test_bonus_not_applied_in_green(self):
        """Catalyst bonus is only active in YELLOW/RED."""
        _, eff_with, _ = _regime_gate("BUY", 0.60, "GREEN", signal_type="EpisodicPivot")
        _, eff_without, _ = _regime_gate("BUY", 0.60, "GREEN")
        assert eff_with == eff_without  # no bonus applied in GREEN

    def test_momentum_burst_no_bonus(self):
        """Trend-continuation patterns receive no bonus."""
        _, eff, _ = _regime_gate("BUY", 0.78, "RED", signal_type="MomentumBurst")
        assert eff == pytest.approx(0.78, abs=1e-9)

    def test_elephant_bar_no_bonus(self):
        _, eff, _ = _regime_gate("BUY", 0.78, "RED", signal_type="ElephantBar")
        assert eff == pytest.approx(0.78, abs=1e-9)

    def test_vcp_no_bonus(self):
        _, eff, _ = _regime_gate("BUY", 0.78, "RED", signal_type="VCP")
        assert eff == pytest.approx(0.78, abs=1e-9)

    def test_high_tight_flag_no_bonus(self):
        _, eff, _ = _regime_gate("BUY", 0.78, "RED", signal_type="HighTightFlag")
        assert eff == pytest.approx(0.78, abs=1e-9)

    def test_bonus_capped_at_1_0(self):
        """Effective confidence cannot exceed 1.0."""
        _, eff, _ = _regime_gate("BUY", 0.99, "RED", signal_type="EpisodicPivot")
        assert eff == pytest.approx(1.0, abs=1e-9)

    def test_bonus_on_sell_in_red(self):
        """Bonus can apply to SELL too — effective_confidence is returned correctly."""
        _, eff, _ = _regime_gate("SELL", 0.40, "RED", signal_type="EpisodicPivot")
        # 0.40 + 0.10 = 0.50 > 0.45 (RED SELL threshold) → passes
        assert eff == pytest.approx(0.50, abs=1e-9)


# ============================================================================
# None / unknown regime fallback
# ============================================================================
class TestRegimeFallback:
    def test_none_regime_defaults_to_green_thresholds(self):
        """No Intel Bus data → fall back to GREEN (permissive)."""
        blocked, _, _ = _regime_gate("BUY", 0.60, None)
        assert not blocked  # 0.60 >= 0.55 (GREEN threshold)

    def test_none_regime_blocks_below_green_threshold(self):
        blocked, _, _ = _regime_gate("BUY", 0.50, None)
        assert blocked  # 0.50 < 0.55

    def test_unknown_regime_string_defaults_to_green(self):
        blocked, _, _ = _regime_gate("BUY", 0.60, "UNKNOWN_REGIME")
        assert not blocked

    def test_none_regime_no_catalyst_bonus(self):
        """Bonus only applies in YELLOW/RED, not in the GREEN fallback."""
        _, eff_with, _ = _regime_gate("BUY", 0.60, None, signal_type="EpisodicPivot")
        _, eff_without, _ = _regime_gate("BUY", 0.60, None)
        assert eff_with == eff_without


# ============================================================================
# Reason string content
# ============================================================================
class TestReasonString:
    def test_blocked_reason_contains_confidence(self):
        blocked, _, reason = _regime_gate("BUY", 0.60, "RED")
        assert blocked
        assert "confidence=0.60" in reason

    def test_blocked_reason_contains_required_threshold(self):
        blocked, _, reason = _regime_gate("BUY", 0.60, "RED")
        assert blocked
        assert "0.85" in reason

    def test_blocked_reason_contains_regime(self):
        blocked, _, reason = _regime_gate("BUY", 0.60, "RED")
        assert blocked
        assert "RED" in reason

    def test_pass_has_empty_reason(self):
        blocked, _, reason = _regime_gate("BUY", 0.90, "RED")
        assert not blocked
        assert reason == ""

    def test_catalyst_bonus_shown_in_blocked_reason(self):
        """When bonus applied but still insufficient, reason includes catalyst name."""
        blocked, _, reason = _regime_gate("BUY", 0.74, "RED", signal_type="EpisodicPivot")
        assert blocked
        assert "EpisodicPivot" in reason

    def test_catalyst_bonus_not_in_reason_when_no_bonus(self):
        """No bonus → no catalyst info in reason."""
        blocked, _, reason = _regime_gate("BUY", 0.60, "RED")
        assert blocked
        assert "catalyst" not in reason

    def test_pass_with_bonus_has_empty_reason(self):
        """Signal that passes (with bonus) produces empty reason."""
        blocked, _, reason = _regime_gate("BUY", 0.78, "RED", signal_type="EpisodicPivot")
        assert not blocked
        assert reason == ""


# ============================================================================
# Case insensitivity
# ============================================================================
class TestCaseInsensitivity:
    def test_lowercase_buy(self):
        blocked_upper, _, _ = _regime_gate("BUY", 0.60, "RED")
        blocked_lower, _, _ = _regime_gate("buy", 0.60, "RED")
        assert blocked_upper == blocked_lower

    def test_lowercase_sell(self):
        blocked_upper, _, _ = _regime_gate("SELL", 0.45, "RED")
        blocked_lower, _, _ = _regime_gate("sell", 0.45, "RED")
        assert blocked_upper == blocked_lower

    def test_mixed_case_short(self):
        blocked_upper, _, _ = _regime_gate("SHORT", 0.50, "YELLOW")
        blocked_mixed, _, _ = _regime_gate("Short", 0.50, "YELLOW")
        assert blocked_upper == blocked_mixed
