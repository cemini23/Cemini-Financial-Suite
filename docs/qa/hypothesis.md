# Property-Based Testing (Hypothesis)

Property-based testing with [Hypothesis](https://hypothesis.readthedocs.io/) validates
that Cemini's financial algorithms behave correctly across the full input space, not just
hand-picked test cases. This catches edge cases that example-based tests miss — such as
zero-division in position sizing when the win rate is exactly 1.0, or NaN propagation in
CVaR when all returns are identical.

---

## What Is Property-Based Testing?

Instead of writing:

```python
def test_kelly_with_50pct_win_rate():
    k = FractionalKelly(fraction=0.25)
    assert k.calculate(0.5, 2.0) == pytest.approx(0.125)
```

Hypothesis generates hundreds of random valid inputs and checks that properties
hold for all of them:

```python
from hypothesis import given, strategies as st

@given(
    win_rate=st.floats(min_value=0.01, max_value=0.99),
    reward_risk=st.floats(min_value=0.1, max_value=10.0),
)
def test_kelly_fraction_never_exceeds_cap(win_rate, reward_risk):
    k = FractionalKelly(fraction=0.25)
    result = k.calculate(win_rate, reward_risk)
    assert 0.0 <= result <= 0.25  # property: never exceeds cap
```

---

## Covered Modules

### Risk Engine (`trading_playbook/risk_engine.py`)

| Property | Description |
|---|---|
| Kelly fraction ≤ cap | Position size never exceeds `fraction` parameter |
| Kelly fraction ≥ 0 | No negative position sizes |
| CVaR ≤ 0 | Expected shortfall is always a loss (non-positive) |
| CVaR dominates VaR | At 99th percentile, CVaR ≤ VaR |
| DrawdownMonitor monotonic peak | Peak value never decreases |
| Halt triggers on threshold breach | `check()` returns `True` when drawdown exceeds threshold |

### Signal Detectors (`trading_playbook/signal_catalog.py`)

| Property | Description |
|---|---|
| Confidence in [0, 1] | All detectors return confidence within valid range |
| Entry price > 0 | Entry price is always positive |
| Stop price < Entry price | Stop is always below entry (bullish setups) |
| None on insufficient data | Detectors return `None` for DataFrames below `min_rows` |
| Idempotent | Same input always produces same output |

### Pydantic Contracts (`cemini_contracts/`)

| Property | Description |
|---|---|
| Round-trip serialization | `safe_validate(safe_dump(x)) == x` for all contracts |
| Validation rejects invalid types | Wrong types always raise `ValidationError` |
| Timestamps are UTC | All datetime fields serialize as UTC ISO-8601 |

---

## Running Hypothesis Tests

```bash
# All property tests
python3 -m pytest tests/ -k "hypothesis" -v

# With verbose Hypothesis output
python3 -m pytest tests/test_hypothesis_risk_engine.py -v \
  --hypothesis-show-statistics
```

Hypothesis maintains a database of failing examples at `.hypothesis/` — once a
failure is found, it's replayed on every subsequent run until the code is fixed.

---

## Configuration

Hypothesis settings in `tests/conftest.py`:

```python
from hypothesis import settings, HealthCheck

settings.register_profile("ci", max_examples=50, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=200)
settings.load_profile("ci")
```

CI runs 50 examples per property (fast). Local dev runs 200 for deeper coverage.

---

## Example: CVaR edge case caught by Hypothesis

Hypothesis discovered that `CVaRCalculator.calculate()` raised `IndexError` when passed
a list of identical returns (all elements equal, so the 99th-percentile slice is empty).
The fix added a guard:

```python
tail = sorted_returns[:max(1, n_tail)]  # never empty
```

This edge case would never appear in example-based tests — Hypothesis found it by
generating `[0.01] * 100`.
