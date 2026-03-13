# Cemini Financial Suite — Test Suite

## Overview

538+ pure pytest tests covering all critical trading logic, data contracts,
and infrastructure. All tests are pure (no network, no Redis, no Postgres).

Step 42 adds four advanced testing dimensions for IP-sale due diligence:
- **42a** Schemathesis API fuzz testing from OpenAPI specs
- **42b** Hypothesis property-based tests for mathematical invariants
- **42c** mutmut mutation testing (proves tests verify behavior, not just pass)
- **42d** VCR.py HTTP cassette recording for deterministic API replay

---

## Test Categories

| Marker | Files | Description | CI? |
|--------|-------|-------------|-----|
| `unit` | `test_*.py` (all) | Pure unit tests (no I/O) | ✅ default |
| `property` | `test_property_based.py`, `test_hypothesis_intel.py` | Hypothesis property-based tests | ✅ default |
| `cassette` | `test_vcr_fred.py` | VCR.py recorded HTTP replay tests | ✅ default |
| `fuzz` | `test_api_fuzz.py` | Schemathesis API fuzz (requires live services) | ❌ manual |
| `slow` | *(none currently)* | Tests taking >5 seconds | ❌ manual |

---

## Quick Commands

```bash
# Standard CI run (parallel, excludes fuzz + slow)
python3 -m pytest tests/ -n auto -m "not fuzz" -q --timeout=60

# Run only property-based tests
python3 -m pytest tests/ -m property -v

# Run only cassette tests
python3 -m pytest tests/ -m cassette -v

# Full suite script (handles flags)
./scripts/run_tests.sh          # default: parallel, no fuzz
./scripts/run_tests.sh --serial # disable -n auto (debug ordering issues)

# API fuzz testing (requires running Docker services)
./scripts/run_fuzz.sh [kalshi|screener|mcp|all]

# Mutation testing (10–30 min, manual quality audit)
./scripts/run_mutations.sh [risk_engine|macro_regime|fred_monitor|all]

# Re-record VCR cassettes (requires API keys + network)
VCR_RECORD_MODE=new_episodes python3 -m pytest tests/ -m cassette
```

---

## File Map

| File | Tests | What it covers |
|------|-------|----------------|
| `test_trading_playbook.py` | ~80 | Risk engine, regime, signals, kill switch |
| `test_property_based.py` | ~50 | Hypothesis: Kelly, CVaR, drawdown, regime, Pydantic |
| `test_hypothesis_intel.py` | ~30 | Hypothesis: Intel bus payload serialization |
| `test_fred_monitor.py` | 26 | FRED scraper: parsing, TTL, DB, archive |
| `test_vcr_fred.py` | ~15 | VCR cassette replay for FRED HTTP interactions |
| `test_api_fuzz.py` | 5 | Schemathesis config (skipped in CI — live services) |
| `test_contracts.py` | ~50 | Pydantic v2 model validation |
| `test_opportunity_screener.py` | ~70 | Discovery engine, conviction scorer |
| `test_safety_guards.py` | ~20 | C4/C5/C7 safety guards |
| `test_vector_intelligence.py` | ~50 | pgvector + CRAG retrieval |
| `tests/conftest.py` | — | Markers, VCR fixture |

---

## VCR Cassettes

Cassettes in `tests/fixtures/vcr_cassettes/` are YAML files recording HTTP
responses. CI replays them — no network or API key needed.

- `fred_t10y2y.yaml` — T10Y2Y yield spread (includes a `"."` sentinel value)
- `fred_dff.yaml` — Effective fed funds rate (DFF)

**Re-recording:** Set `VCR_RECORD_MODE=new_episodes` and run with valid API keys.
API keys are automatically scrubbed from cassettes by `_scrub_request()` in conftest.py.

---

## Mutation Testing

Run `./scripts/run_mutations.sh` to execute mutmut on critical modules.
Target score: **>= 80% killed** on each module.

After running:
```bash
mutmut results           # summary: killed / survived / suspicious
mutmut show <id>         # inspect a surviving mutant
mutmut junitxml          # generate tests/mutation_report.xml
```

Modules targeted:
- `trading_playbook/risk_engine.py` — FractionalKelly, CVaR, DrawdownMonitor
- `trading_playbook/macro_regime.py` — GREEN/YELLOW/RED classifier
- `core/intel_bus.py` — IntelPublisher/IntelReader
- `scrapers/fred_monitor.py` — FRED parsing logic

---

## Hypothesis Configuration

Property tests use Hypothesis with 80–200 examples per test.
Settings are `@settings(max_examples=N, suppress_health_check=[HealthCheck.too_slow])`.

If a property test fails, Hypothesis prints the minimal failing example.
Fix the underlying invariant, not just the test.

---

## pytest-xdist Parallel Execution

Default: `-n auto` (uses all available CPU cores).
Each test must be stateless — no shared mutable state, no file system conflicts.

If a test fails with `-n auto` but passes serially, check for:
1. Shared global state being mutated
2. File path conflicts (use `tmp_path` fixture)
3. Import-time side effects
