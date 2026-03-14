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
**File:** `agents/orchestrator.py:140`
**Severity:** High
**Status:** Known, unresolved

`publish_signal_to_bus()` returns `{"execution_status": "NO_ACTION_TAKEN"}` without
ever publishing to Redis. The LangGraph brain generates trade verdicts that silently
die — no trade ever reaches the EMS through the orchestrator path.

**Planned fix:** Wire `IntelPublisher.publish()` to the `trade_signals` Redis channel
in `publish_signal_to_bus()`. The Trading Playbook (observation-only) bypasses this
path and has no equivalent issue.

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

### C3 — QuantOS Kalshi Adapter Hardcoded Path
**File:** `QuantOS/core/brokers/kalshi.py:24`
**Severity:** High
**Status:** Known, unresolved

Hardcoded path `/Users/<username>/Desktop/Kalshi by Cemini` breaks in any Docker
container or non-Mac environment. The QuantOS Kalshi adapter cannot work in
production as-is.

**Planned fix:** Replace with environment variable `KALSHI_CERT_PATH`.

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

---

## Summary

| Category | Count |
|---|---|
| Critical (pre-live blockers) | 4 |
| Medium | 4 |
| Low | 3 |
| **Total open** | **11** |
| Resolved | 7 |
