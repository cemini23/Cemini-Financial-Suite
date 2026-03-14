# Test Suite Overview

Cemini Financial Suite maintains a comprehensive test suite with **754+ passing tests** across
unit, property-based, fuzz, mutation, and integration categories. All tests are pure
(no network, no live Redis/Postgres) and run in parallel via pytest-xdist.

---

## Test Inventory

| Category | File Pattern | Count (approx) | Description |
|---|---|---|---|
| Unit | `tests/test_*.py` | ~560 | Core business logic, data models, utilities |
| Audit Trail | `tests/test_audit_trail.py` | 66 | Hash chain, Merkle batch, OTS, intent logging |
| Property-Based | `tests/test_hypothesis_*.py` | ~30 | Hypothesis: risk engine, signal detectors |
| API Fuzz | `tests/test_api_fuzz.py` | ~20 | Schemathesis: QuantOS, Kalshi, MCP endpoints |
| EDGAR | `tests/test_edgar*.py` | 38 | SEC EDGAR pipeline, Form 4, XBRL |
| Resilience | `tests/test_resilience*.py` | ~25 | Circuit breaker, retry, dead-letter queue |
| Documentation | `tests/test_docs.py` | 16 | MkDocs nav integrity, Mermaid syntax |
| **Total** | | **770+** | All green, ruff clean |

---

## Running the Suite

### Full suite (parallel)

```bash
python3 -m pytest tests/ -v -n auto --tb=short
```

`-n auto` activates pytest-xdist, which spawns one worker per CPU core.
The full suite completes in **< 30 seconds** on a 4-core machine.

### Single category

```bash
# Unit tests only
python3 -m pytest tests/ -v --ignore=tests/test_api_fuzz.py -n auto

# Documentation tests only
python3 -m pytest tests/test_docs.py -v

# Audit trail only
python3 -m pytest tests/test_audit_trail.py -v
```

### With coverage

```bash
python3 -m pytest tests/ -v -n auto --cov=. --cov-report=html
# Coverage report at htmlcov/index.html
```

---

## Test Design Principles

### 1. Pure (no I/O)

Tests mock all external dependencies — Redis, Postgres, HTTP calls, filesystem.
This ensures:
- Tests run offline (no Polygon/FRED/EDGAR API needed)
- Tests run identically in CI and local dev
- Tests are fast (no network latency)

```python
# Example: mocking Redis in audit trail tests
@mock.patch("shared.audit_trail.chain_writer.redis.Redis")
def test_chain_writer_publishes_to_intel_bus(mock_redis_cls):
    mock_client = mock.MagicMock()
    mock_redis_cls.return_value = mock_client
    # ... test logic
    mock_client.set.assert_called_once()
```

### 2. Deterministic

No `time.sleep()`, no randomness without seeding, no flaky network-dependent assertions.
pytest-timeout guards (default 30s per test) prevent hangs.

### 3. Coverage Over Key Boundaries

Tests focus on:
- **Financial math**: Kelly sizing, CVaR, RSI, regime classification
- **Audit integrity**: hash chain linkage, Merkle root consistency, UUIDv7 ordering
- **Signal detection**: all 6 detectors with boundary conditions
- **Resilience**: circuit breaker open/half-open/close transitions, retry backoff
- **Data contracts**: Pydantic model validation at all Intel Bus boundaries

---

## CI Integration

Tests run automatically on every push to `main`:

```yaml
- name: Run test suite (parallel, exclude fuzz)
  run: python3 -m pytest tests/ -v -n auto --ignore=tests/test_api_fuzz.py
```

Fuzz tests (`test_api_fuzz.py`) are excluded from CI because Schemathesis requires live
FastAPI endpoints. They run manually against a running stack.

See [CI/CD Pipeline](ci-cd.md) for full pipeline details.

---

## Mutation Testing (mutmut)

Step 42 added mutation testing via `mutmut` to validate test quality:

```bash
mutmut run --paths-to-mutate=trading_playbook/risk_engine.py
mutmut results
```

Mutation score target: **>80%** for core financial logic modules.
See [Mutation Testing](mutmut.md) for details.

---

## Skipped Tests

7 tests are currently skipped (marked `@pytest.mark.skip`):
- Tests requiring live Schemathesis endpoints (skip in pure CI)
- One VCR cassette test pending cassette recording

These are tracked in the [Technical Debt Register](../appendices/tech-debt.md).
