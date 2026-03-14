# Mutation Testing (mutmut)

[mutmut](https://mutmut.readthedocs.io/) validates test quality by systematically
introducing small bugs ("mutations") into the source code and checking whether the
test suite catches them. A test suite that can't detect mutations is too weak to be
trusted, even if it has high line coverage.

---

## Why Mutation Testing?

Line coverage tells you which code was executed; mutation testing tells you which
code was **verified**. Consider:

```python
def calculate_stop(entry: float, atr: float) -> float:
    return entry - 2 * atr  # ATR-based stop
```

A test that calls `calculate_stop(100, 5)` and asserts the result is `90.0` has
100% line coverage. But mutation testing will try:

- `entry - 2 * atr` → `entry + 2 * atr` (arithmetic mutation)
- `entry - 2 * atr` → `entry - 1 * atr` (constant mutation)
- `entry - 2 * atr` → `entry - 3 * atr`

If the test catches all three → **mutation killed** (good).
If the test misses any → **mutation survived** (weak assertion).

---

## Target Modules

High-priority modules for mutation testing:

| Module | Mutation Score Target | Rationale |
|---|---|---|
| `trading_playbook/risk_engine.py` | >85% | Financial math — Kelly, CVaR, drawdown |
| `trading_playbook/signal_catalog.py` | >80% | Signal detection logic |
| `trading_playbook/kill_switch.py` | >80% | Safety-critical halt conditions |
| `shared/audit_trail/hasher.py` | >90% | Cryptographic correctness |
| `trading_playbook/macro_regime.py` | >80% | Regime classification |

---

## Running mutmut

```bash
# Install
pip3 install mutmut

# Run on risk engine (fast — focused target)
mutmut run --paths-to-mutate=trading_playbook/risk_engine.py

# View results
mutmut results

# Show surviving mutations (weak spots)
mutmut show <id>

# HTML report
mutmut html
```

Configuration in `mutmut_config.py`:

```python
def pre_mutation(context):
    # Skip mutations in pure logging lines (not worth testing)
    if "logger." in context.current_source_line:
        context.skip = True
```

---

## Interpreting Results

```
Mutation score [####        ] 73/90 (81.1%)
Killed: 73
Survived: 14
Skipped: 3
```

| Status | Meaning |
|---|---|
| **Killed** | Test suite caught the bug ✅ |
| **Survived** | Test suite missed the mutation — weak assertion |
| **Skipped** | Mutation was syntactically equivalent or excluded |

A "survived" mutation indicates either a missing assertion or dead code that isn't
exercised by any test path.

---

## Example Fix

mutmut revealed that the `FractionalKelly.calculate()` return was not fully
asserted — tests checked the result was positive but not that it matched the
exact Kelly formula. Adding a `pytest.approx` check killed the surviving mutation:

```python
# Before: weak assertion
assert result > 0

# After: strong assertion (kills constant/arithmetic mutations)
assert result == pytest.approx(expected_kelly * 0.25, rel=1e-6)
```

---

## CI Integration

mutmut is not run in CI (too slow for every push — a full run takes ~10 minutes).
It runs as a pre-release quality gate, documented in the release checklist.

See [Test Suite Overview](test-suite.md) for the full testing picture.
