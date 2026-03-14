# Technical Debt Register

This register documents all known issues, incomplete implementations, and architectural
decisions that will need to be addressed before live trading deployment. Cemini is
currently in **paper trading mode** — no live equity or cryptocurrency orders are placed.

Transparency about known issues is a feature, not a bug: it tells a buyer exactly
what remains to be completed and prevents surprises during integration.

---

## Critical Issues (Pre-Live Blockers)

These issues **must** be resolved before any live trading:

### C1 — Orchestrator Signal Bus Dead End
**File:** `agents/orchestrator.py`
**Severity:** High
**Status:** RESOLVED (Mar 14, 2026)

`publish_signal_to_bus()` now guards Redis publishing behind `ENABLE_BRAIN_PUBLISH=true`
(default: false). When enabled, EXECUTE verdicts are serialized to JSON and published
to `trade_signals` Redis channel. Redis failures are caught and never crash the
orchestrator. Returns `PUBLISH_DISABLED` (guard off) or `SIGNAL_PUBLISHED` (success).

---

### C2 — Hardcoded CIO Debate Node
**File:** `agents/orchestrator.py:73-86`
**Severity:** High
**Status:** Known, unresolved

The CIO debate node is 100% hardcoded: `confidence = 0.85`, `action = "BUY"`. There
is no LLM call despite an extensive prompt comment. The `pydantic_signal` field in
`TradingState` is never populated, which would cause a `KeyError` when the schema
is eventually consumed.

**Planned fix:** Implement actual LangGraph Claude API call in the debate node.
Replace the hardcoded confidence with a Bayesian conviction scorer output.

---

### C3 — Hardcoded Mac Path in verify_install.py
**File:** `QuantOS/scripts/verify_install.py`
**Severity:** High
**Status:** RESOLVED (Mar 14, 2026)

Hardcoded `/Users/claudiobarone/Desktop/QuantOS` path replaced with
`os.getenv("QUANTOS_ROOT", <relative_fallback>)`. The fallback derives from
`__file__` so it works in Docker and any environment. Set `QUANTOS_ROOT=/opt/cemini/QuantOS`
in Docker env to override.

---

### C6 — Fictional Buying Power in EMS Kalshi Adapter
**File:** `core/ems/adapters/kalshi_fix.py:23-24`
**Severity:** High
**Status:** Known, unresolved

`get_buying_power()` always returns `1000.00` (hardcoded). Position sizing through
this adapter is based on a fictional balance. In paper trading mode this is harmless;
in live mode it would cause incorrect position sizes.

**Planned fix:** Call Kalshi's balance API endpoint and cache the result (5-minute TTL).

---

## Logic and Architecture Issues (L/A-series) — All Resolved

### L3 — check_exposure() Hard-Block Not Wired
**File:** `QuantOS/core/execution.py`
**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

Exposure check now supports `HARD_BLOCK_EXPOSURE=true` env var (default: false =
observation mode). In observation mode, exposure failures log a warning but do not
block the trade. With `HARD_BLOCK_EXPOSURE=true`, trades are hard-blocked on exposure
breach.

---

### L4 — strategy_mode Win-Rate Only, Not Regime-Driven
**File:** `analyzer.py`
**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

`strategy_mode` now driven by regime from `intel:playbook_snapshot` via
`_get_current_regime_from_redis()` + `_regime_to_strategy_mode()` helpers.
GREEN=aggressive, YELLOW=sniper, RED=conservative. Win-rate still computed for
Discord reporting but no longer controls mode.

---

### A4 — BigQuery Table Name Default Mismatch
**Severity:** Low
**Status:** RESOLVED — already consistent (Mar 14, 2026)

`QuantOS/core/harvester.py` and `QuantOS/core/bq_signals.py` both default to
`"market_ticks"`. No code change required; confirmed consistent.

---

### A6 — executed_trades Not Redis-Backed (QuantOS Engine)
**File:** `QuantOS/core/engine.py`
**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

`TradingEngine` now initializes `self.executed_trades` from Redis on startup via
`_load_executed_trades_from_redis()`. Each successful trade is written to
`quantos:executed_trades` (24h TTL) via `_save_trade_to_redis()`. Trade history
survives container restarts.

---

### S5 — Duplicate ib_insync Imports
**File:** `QuantOS/core/brokers/router.py`
**Severity:** Low
**Status:** NOT APPLICABLE (Mar 14, 2026)

No ib_insync imports exist in router.py. Only one ib_insync import found
in `ibkr.py` at module level — correct. Issue was not present in current code.

---

## Medium Issues (Post-Live Improvements)

These are not blockers for paper trading but should be resolved in early production:

### M1 — Social Alpha Uses Simulated Tweets
**File:** `modules/social_alpha/analyzer.py:76-80`
**Guard:** `SOCIAL_ALPHA_LIVE=true` (Step 33)
**Status:** Known, gated

`get_target_sentiment()` uses hardcoded simulated tweets rather than live X API data.
The `SOCIAL_ALPHA_LIVE` env var guard prevents live signals from flowing unless
explicitly enabled. When `SOCIAL_ALPHA_LIVE=false` (default), social signals emit
neutral/zero-conviction output.

**Planned fix:** Implement live X API integration (requires X API access tier 2+).

---

### M2 — Weather Alpha Uses Simulated Kalshi Prices
**File:** `modules/weather_alpha/analyzer.py:18-20`
**Guard:** `WEATHER_ALPHA_LIVE=true` (Step 33)
**Status:** Known, gated

Kalshi order book prices for weather contract arbitrage calculations are simulated
(`"price": 0.15`). The `WEATHER_ALPHA_LIVE` guard prevents live signals.

**Planned fix:** Fetch live Kalshi market prices via the Kalshi API for weather contracts.

---

### M3 — ruff format Drift (196 Files)
**Scope:** Entire codebase
**Status:** Non-blocking (CI allows format drift)

`ruff format --check .` reports 196 files with formatting drift from the Step 34c
migration (flake8 → ruff). The `ruff check .` (lint) passes; only format drift is
present. Auto-formatting is a separate cleanup PR to avoid a large noise commit.

**Planned fix:** Single PR: `ruff format .` + commit.

---

### M4 — 7 Skipped Tests
**File:** Various
**Status:** Known, tracked

7 tests are marked `@pytest.mark.skip`:
- Schemathesis fuzz tests (require live services, not appropriate for pure CI)
- 1 VCR.py cassette test (cassette not yet recorded)

**Planned fix:** Record VCR cassettes; move schemathesis to a separate CI job with
a Docker-compose test stack.

---

## Low Priority (IP Sale Enhancement Items)

### L1 — kalshi_autopilot Container Not Running
**Status:** Pre-existing

The `kalshi_autopilot` Prometheus scrape target shows DOWN. The container is not
running. Code is baked into the image; it requires a rebuild after any code change.

### L2 — Grafana Alertmanager Target
**Status:** Functional

Alertmanager is deployed but only triggers internal Grafana alerts (no PagerDuty,
Slack, or email integration). Production deployment should add notification receivers.

### L3 — OTS Timestamps Pending Confirmation
**Status:** Expected

OpenTimestamps proofs stamped in the last 1–6 hours will show as "pending" (awaiting
Bitcoin block confirmation). This is expected behavior, not a bug.
See [OpenTimestamps](../verification/opentimestamps.md).

---

## Resolved Issues (FYI)

| ID | Issue | Resolution | Commit |
|---|---|---|---|
| C4 | Hardcoded DB password | `POSTGRES_PASSWORD` env var + guard | Step 33 |
| C5 | Live social signal gate | `SOCIAL_ALPHA_LIVE` env var guard | Step 33 |
| C7 | Live weather signal gate | `WEATHER_ALPHA_LIVE` env var guard | Step 33 |
| — | RSI using SMA (wrong) | Wilder SMMA (correct) | Mar 8 |
| — | Redis TTL mismatch (nil intel) | Publish every 4 min, TTL=5 min | fb8e1d6 |
| — | Regime gate wrong (sniper=bearish) | sniper → "neutral" | fb8e1d6 |
| — | `fresh_start_pending` trigger | Redis-backed, explicit-only | Mar 8 |
| C1 | Orchestrator publish dead path | `ENABLE_BRAIN_PUBLISH` guard + wire | Mar 14 |
| C3 | Mac-only path in verify_install.py | `os.getenv("QUANTOS_ROOT")` + `__file__` fallback | Mar 14 |
| L3 | check_exposure() never blocks | `HARD_BLOCK_EXPOSURE` env var gate | Mar 14 |
| L4 | strategy_mode win-rate only | Regime-based via `_get_current_regime_from_redis()` | Mar 14 |
| A4 | BQ_TABLE_ID default mismatch | Already consistent (`market_ticks`) | Mar 14 |
| A6 | executed_trades not Redis-backed | `_load_executed_trades_from_redis()` on startup | Mar 14 |
| S5 | Duplicate ib_insync imports | Not applicable — no duplicates in current code | Mar 14 |
| — | CVaR test all-positive returns | `assume(any(r < 0 for r in returns))` filter | Mar 14 |

---

## Summary

| Category | Count |
|---|---|
| Critical (pre-live blockers) | 2 (C2, C6) |
| Medium | 4 |
| Low | 3 |
| **Total open** | **9** |
| Resolved | 14 |
