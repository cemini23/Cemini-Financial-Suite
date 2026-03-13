"""Hypothesis property tests for Intel bus payloads (Step 42b).

Tests that Redis intel:* payloads are always JSON-serializable and
preserve value fidelity across the publish/read cycle.

Run: python3 -m pytest tests/test_hypothesis_intel.py -m property -v
"""

import json
import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pytestmark = [pytest.mark.property]

# ── Shared strategies ──────────────────────────────────────────────────────────

_fred_channels = st.sampled_from([
    "intel:fred_yield_curve",
    "intel:fred_credit_spread",
    "intel:fred_labor",
    "intel:fred_inflation",
    "intel:fred_sentiment",
    "intel:fred_fed_policy",
])

_all_channels = st.sampled_from([
    "intel:fred_yield_curve",
    "intel:fred_credit_spread",
    "intel:playbook_snapshot",
    "intel:spy_trend",
    "intel:vix_level",
    "intel:social_score",
    "intel:btc_sentiment",
    "intel:macro_regime",
])

_finite_float = st.floats(
    min_value=-1e9, max_value=1e9,
    allow_nan=False, allow_infinity=False,
)


# ══════════════════════════════════════════════════════════════════════════════
# Intel Bus envelope properties
# ══════════════════════════════════════════════════════════════════════════════

class TestIntelPayloadProperties:
    """Intel payloads must be JSON-serializable and preserve value fidelity."""

    @given(
        value=_finite_float,
        channel=_all_channels,
        source=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=200)
    def test_scalar_payload_json_roundtrip(self, value, channel, source):
        """Scalar float values must survive JSON encode/decode."""
        payload = {
            "value": value,
            "source_system": source,
            "timestamp": 1741824000.0,
            "confidence": 1.0,
        }
        raw = json.dumps(payload)
        parsed = json.loads(raw)
        assert math.isclose(parsed["value"], value, rel_tol=1e-9, abs_tol=1e-15)

    @given(
        spread_10y2y=st.one_of(st.none(), st.floats(-5, 5, allow_nan=False)),
        spread_10y3m=st.one_of(st.none(), st.floats(-5, 5, allow_nan=False)),
        obs_date=st.just("2026-03-12"),
    )
    @settings(max_examples=150)
    def test_fred_yield_curve_payload_serializable(self, spread_10y2y, spread_10y3m, obs_date):
        """FRED yield curve payload with optional None fields serializes cleanly."""
        inner = {k: v for k, v in {
            "spread_10y2y": spread_10y2y,
            "spread_10y3m": spread_10y3m,
            "observation_date": obs_date,
            "source": "fred",
        }.items() if v is not None}

        envelope = {
            "value": inner,
            "source_system": "fred_monitor",
            "timestamp": 1741824000.0,
            "confidence": 1.0,
        }
        raw = json.dumps(envelope)
        parsed = json.loads(raw)

        assert parsed["source_system"] == "fred_monitor"
        assert "value" in parsed
        assert isinstance(parsed["value"], dict)

    @given(
        values=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
            values=st.one_of(
                _finite_float,
                st.text(max_size=50),
                st.none(),
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_dict_payload_value_is_json_safe(self, values):
        """Any dict value (excluding NaN/Inf) must survive JSON round-trip."""
        clean = {k: v for k, v in values.items() if not isinstance(v, float) or math.isfinite(v)}
        envelope = {"value": clean, "source_system": "test", "timestamp": 1.0, "confidence": 1.0}
        raw = json.dumps(envelope)
        parsed = json.loads(raw)
        assert isinstance(parsed["value"], dict)


# ══════════════════════════════════════════════════════════════════════════════
# IntelPayload Pydantic contract — round-trip with complex values
# ══════════════════════════════════════════════════════════════════════════════

class TestIntelPayloadPydantic:
    """IntelPayload must round-trip through Pydantic v2 model_dump/validate."""

    @given(
        value=st.one_of(
            _finite_float,
            st.text(max_size=50),
            st.booleans(),
        ),
        source_system=st.text(min_size=1, max_size=50),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=150)
    def test_intel_payload_model_roundtrip(self, value, source_system, confidence):
        """IntelPayload model_dump → model_validate must preserve all fields."""
        from cemini_contracts.intel import IntelPayload

        p = IntelPayload(value=value, source_system=source_system, confidence=confidence)
        dumped = p.model_dump()
        rebuilt = IntelPayload.model_validate(dumped)

        assert rebuilt.source_system == p.source_system
        assert abs(rebuilt.confidence - p.confidence) < 1e-9
        # value equality — skip NaN (which != NaN by definition)
        if isinstance(value, float) and not math.isfinite(value):
            return
        assert rebuilt.value == p.value

    @given(confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=100)
    def test_intel_payload_confidence_preserved(self, confidence):
        """Confidence value must be exactly preserved through model round-trip."""
        from cemini_contracts.intel import IntelPayload

        p = IntelPayload(value=0.5, source_system="test", confidence=confidence)
        assert p.confidence == confidence


# ══════════════════════════════════════════════════════════════════════════════
# FRED contracts — value field invariants
# ══════════════════════════════════════════════════════════════════════════════

class TestFredContractProperties:
    """FRED Pydantic contracts must handle all numeric ranges FRED can return."""

    @given(
        fed_funds_rate=st.one_of(st.none(), st.floats(0.0, 25.0, allow_nan=False)),
        fed_balance_sheet=st.one_of(st.none(), st.floats(1e6, 1e8, allow_nan=False, allow_infinity=False)),
    )
    @settings(max_examples=100)
    def test_fred_fed_policy_roundtrip(self, fed_funds_rate, fed_balance_sheet):
        """FredFedPolicyIntel round-trips all numeric ranges."""
        from cemini_contracts.fred import FredFedPolicyIntel

        model = FredFedPolicyIntel(
            fed_funds_rate=fed_funds_rate,
            fed_balance_sheet_mm=fed_balance_sheet,
            observation_date="2026-03-12",
        )
        data = model.model_dump()
        rebuilt = FredFedPolicyIntel.model_validate(data)
        assert rebuilt.source == "fred"
        assert rebuilt.observation_date == "2026-03-12"

    @given(
        initial_claims=st.one_of(st.none(), st.floats(100_000, 1_000_000, allow_nan=False, allow_infinity=False)),
        unemployment_rate=st.one_of(st.none(), st.floats(0.0, 30.0, allow_nan=False)),
    )
    @settings(max_examples=100)
    def test_fred_labor_roundtrip(self, initial_claims, unemployment_rate):
        """FredLaborIntel handles the full realistic range of labor indicators."""
        from cemini_contracts.fred import FredLaborIntel

        model = FredLaborIntel(
            initial_claims=initial_claims,
            unemployment_rate=unemployment_rate,
            observation_date="2026-03-07",
        )
        data = model.model_dump()
        rebuilt = FredLaborIntel.model_validate(data)
        assert rebuilt.source == "fred"

    @given(
        hy_spread=st.one_of(st.none(), st.floats(0.5, 30.0, allow_nan=False, allow_infinity=False)),
    )
    @settings(max_examples=100)
    def test_fred_credit_spread_roundtrip(self, hy_spread):
        """FredCreditSpreadIntel preserves HY OAS spread values."""
        from cemini_contracts.fred import FredCreditSpreadIntel

        model = FredCreditSpreadIntel(hy_oas_spread=hy_spread, observation_date="2026-03-12")
        rebuilt = FredCreditSpreadIntel.model_validate(model.model_dump())
        assert rebuilt.source == "fred"
        if hy_spread is not None:
            assert rebuilt.hy_oas_spread == hy_spread
