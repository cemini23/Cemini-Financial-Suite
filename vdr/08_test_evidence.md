# Test Suite Evidence

**Date:** March 2026
**Total:** 778+ passing, ~10 skipped

---

## Summary

| Category | Count | Notes |
|----------|-------|-------|
| Unit tests | ~560 | Core business logic, mock I/O |
| Audit trail tests | 66 | Hash chain, Merkle, intent logging |
| Property-based (Hypothesis) | ~30 | FractionalKelly, CVaR, DrawdownMonitor, all 6 signal detectors |
| API fuzz (Schemathesis) | ~20 | QuantOS :8001, Kalshi :8000, MCP :8002 |
| EDGAR pipeline tests | 38 | CIK mapping, Form 4, XBRL fundamentals |
| Resilience tests | ~25 | Circuit breakers, retry logic, dead-letter queue |
| Documentation tests | 24 | MkDocs nav integrity, Mermaid syntax, content quality |
| VDR integrity tests | 26 | Filesystem checks for VDR completeness |

---

## Test Execution

### Standard Run

```bash
python3 -m pytest tests/ -v -n auto
```

- `-n auto`: Parallel execution via pytest-xdist (uses all CPU cores)
- No network required — all external calls are mocked
- No Redis/PostgreSQL required — pure unit tests

### With Coverage

```bash
python3 -m pytest tests/ -n auto --cov=. --cov-report=term-missing
```

### Excluding Fuzz Tests (CI-safe)

```bash
python3 -m pytest tests/ -n auto -m "not fuzz" --timeout=60
```

---

## Property-Based Testing (Hypothesis)

Hypothesis generates hundreds of random inputs to find edge cases in financial
math functions. Key targets:

| Module | Property Tested |
|--------|----------------|
| `risk_engine.FractionalKelly` | Kelly fraction bounded [0, 1] for any valid inputs |
| `risk_engine.CVaRCalculator` | CVaR always >= mean loss for any distribution |
| `risk_engine.DrawdownMonitor` | Drawdown always <= 100% for any price series |
| `signal_catalog` | All 6 signal detectors handle empty/NaN input gracefully |
| `logit_pricing` | Logit-space pricing is numerically stable for extreme inputs |

---

## API Fuzz Testing (Schemathesis)

Schemathesis auto-generates test cases from OpenAPI schemas and fuzzes all endpoints.

| Service | Port | Endpoints Fuzzed |
|---------|------|-----------------|
| QuantOS | 8001 | `/signal`, `/regime`, `/health`, `/metrics` |
| Kalshi by Cemini | 8000 | `/kalshi/signal`, `/health`, `/metrics` |
| Cemini MCP Server | 8002 | All 10 MCP tools |

Fuzz tests are marked `@pytest.mark.fuzz` and excluded from CI (require live services).
Run manually with `python3 -m pytest tests/ -m fuzz`.

---

## Mutation Testing (mutmut)

mutmut introduces controlled mutations (changing `>` to `>=`, removing conditions, etc.)
to verify that tests actually catch bugs rather than just executing code.

Targets:

| Module | Mutation Kill Rate |
|--------|--------------------|
| `risk_engine.py` | >90% |
| `signal_catalog.py` | >90% |
| `kill_switch.py` | >90% |
| `shared/audit_trail/hasher.py` | >90% |

Run: `mutmut run --paths-to-mutate shared/audit_trail/hasher.py` (takes ~5 min)

---

## VCR.py Cassettes

VCR.py records and replays HTTP responses for deterministic testing of external APIs.

Used for:
- FRED API response stability testing (macro data endpoints)
- Polygon.io response format validation

Cassettes stored in `tests/cassettes/`. Not committed to repo (contain API responses).

---

## Skipped Tests

~10 tests are skipped (not failed). Reasons:

- `@pytest.mark.fuzz` — require live services
- `@pytest.mark.slow` — long-running mutation tests excluded from CI
- Platform-specific tests skipped on non-Linux CI runners

---

## CI Integration

Tests run in the `test` job in `.github/workflows/deploy.yml`:

```yaml
needs: [lint, pip-audit]
run: python3 -m pytest tests/ -n auto -m "not fuzz" -q --timeout=60
```

The deploy job requires the test job to pass. No deployment occurs if any
test fails.
