# Known Issues and Technical Debt

This register is maintained transparently so buyers can assess remaining work.
Issues are classified by severity: **Low**, **Medium**, **High**.

Last updated: March 15, 2026 — 10 issues resolved (C1, C3, C6, L1, L2, L3, L4, A4, A6, S5)

---

## Code Issues (C-series)

### C1: Dead Orchestrator Publish Path

**Severity:** Low
**Status:** RESOLVED (Mar 14, 2026)
**Affects:** Paper trading — no functional impact

`publish_signal_to_bus()` in `agents/orchestrator.py` now guards Redis publishing
behind `ENABLE_BRAIN_PUBLISH=true` (default: false). When enabled, signals are
serialized to JSON and published to the `trade_signals` Redis channel. Redis
failures are caught and do not crash the orchestrator. Returns `PUBLISH_DISABLED`
when guard is off, `SIGNAL_PUBLISHED` on success.

---

### C2: CIO Debate Hardcoded

**Severity:** Low
**Status:** Open — planned fix in Step 7 (RL agent)

The "Chief Investment Officer" debate function in the orchestrator uses hardcoded
conviction thresholds rather than a learned policy.

**Fix:** Step 7 (Reinforcement Learning Agent) will replace hardcoded thresholds
with a PPO-trained policy that adapts to market conditions.

---

### C3: macOS-only Path

**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

`QuantOS/scripts/verify_install.py` contained a hardcoded `/Users/claudiobarone/Desktop/QuantOS`
path. Replaced with `os.getenv("QUANTOS_ROOT", <relative_fallback>)` where the
fallback derives from `__file__` so it works in Docker and any environment.
Set `QUANTOS_ROOT=/opt/cemini/QuantOS` in Docker env to override.

---

### C6: Hardcoded Buying Power ($1,000)

**Severity:** Medium
**Status:** RESOLVED (Mar 15, 2026)

`shared/safety/exposure_gate.py` `ExposureGate` now uses `LIVE_TRADING=true` to
switch from the paper trading limit ($1,000 default) to the buying_power value
passed by the broker adapter.  When `LIVE_TRADING` is not set (default),
ExposureGate uses `paper_buying_power=1000.0` as the sizing ceiling.  When set,
callers must pass the real balance from `adapter.get_buying_power()`.
ExposureGate is **fail-closed**: zero/unknown buying power → order blocked.

---

## Logic Issues (L-series)

### L1: Engine Restarts With Empty executed_trades

**Severity:** Medium
**Status:** RESOLVED (Mar 15, 2026)

On service restart, `TradingEngine` came up with an empty `executed_trades` dict,
potentially re-executing already-filled orders before Redis hydration completed.

`shared/safety/state_hydrator.py` `StateHydrator.hydrate()` now provides a
single authoritative call that loads both `executed_trades` and `active_positions`
from Redis before the engine begins processing signals.  Returns `HydratedState`
with `loaded=False` if Redis is unavailable (safe — engine starts clean).

---

### L2: Exposure Gate Was Observation-Only

**Severity:** Medium
**Status:** RESOLVED (Mar 15, 2026)

The per-ticker exposure check in the order path logged warnings but never
hard-blocked orders that would exceed the configured ceiling.

`shared/safety/exposure_gate.py` `ExposureGate.check()` now hard-blocks
(returns `False`) when `current_exposure + proposed_spend > max_exposure`.
This is the default behaviour — no env var override needed.  The gate is
fail-closed: if buying power cannot be determined, the order is blocked.

---

### L3: check_exposure() Never Blocks

**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

`QuantOS/core/execution.py` `execute_buy()` exposure check now supports
`HARD_BLOCK_EXPOSURE=true` env var. Default is observation mode (log warning,
let trade proceed). Set `HARD_BLOCK_EXPOSURE=true` to hard-block on exposure
breach. Previously always returned False on breach with no env override path.

---

### L4: strategy_mode Not Regime-Driven

**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

`analyzer.py` `strategy_mode` was set by win-rate threshold with regime as a
cap/override. Now regime is the primary driver via `_get_current_regime_from_redis()`
and `_regime_to_strategy_mode()` helpers. GREEN=aggressive, YELLOW=sniper,
RED=conservative. Win-rate still computed for Discord reporting.

---

## Architecture Issues (A-series)

### A4: BigQuery Table Name Defaults

**Severity:** Low
**Status:** RESOLVED — already consistent (Mar 14, 2026)

`QuantOS/core/harvester.py` and `QuantOS/core/bq_signals.py` both default to
`"market_ticks"` when `BQ_TABLE_ID` is not set. No code change required; both
were already aligned. Verified by `tests/test_desloppify.py::TestD5BQTableConsistency`.

---

### A6: executed_trades Not Redis-Backed (QuantOS Engine)

**Severity:** Medium
**Status:** RESOLVED (Mar 14, 2026)

`QuantOS/core/engine.py` `TradingEngine` now initializes `self.executed_trades`
from Redis on startup via `_load_executed_trades_from_redis()`. Each successful
trade is written to `quantos:executed_trades` (24h TTL) via `_save_trade_to_redis()`.
Trade history now survives container restarts.

---

## Service Issues (S-series)

### S5: Duplicate ib_insync Imports

**Severity:** Low
**Status:** NOT APPLICABLE (Mar 14, 2026)

`QuantOS/core/brokers/router.py` has no `ib_insync` imports. The only ib_insync
import exists in `QuantOS/core/brokers/ibkr.py` at module level (line 5) — correct.
No duplicates found anywhere in the codebase. Issue was already resolved or
was never present in current code.

---

## Mock Data / Simulation Issues (M-series)

### M1: Social Alpha Simulated Tweets

**Severity:** Low (gated)
**Status:** By design — gated behind `SOCIAL_ALPHA_LIVE=true`

When `SOCIAL_ALPHA_LIVE` is not set, the social alpha harvester returns simulated
tweet data for development/testing. This is a deliberate safety guard (Step 33).

**For live use:** Set `SOCIAL_ALPHA_LIVE=true` and configure the Twitter/X API key.

---

### M2: Weather Alpha Simulated Prices

**Severity:** Low (gated)
**Status:** By design — gated behind `WEATHER_ALPHA_LIVE=true`

When `WEATHER_ALPHA_LIVE` is not set, the weather alpha engine uses simulated
Kalshi contract prices. This is a deliberate safety guard (Step 33).

**For live use:** Set `WEATHER_ALPHA_LIVE=true` and configure the Visual Crossing
API key.

---

## Formatting / Style Debt (M-series continued)

### M3: Ruff Format Drift (196 files)

**Severity:** Low (non-blocking)
**Status:** Open — tracked as cleanup sprint

196 Python files have formatting differences from `ruff format` style
(primarily quote style, trailing commas, line splitting). This is non-blocking —
`ruff check .` passes; `ruff format --check .` shows drift.

**Fix:** Run `ruff format .` across the codebase in a dedicated cleanup PR.
No logic changes — purely cosmetic.

---

## Dependency Issues (D-series)

### D1: pymerkle GPLv3+ (see License Isolation Report)

**Severity:** Medium (legal risk)
**Status:** Open — replaceable

pymerkle is the only pure-GPL runtime dependency. See `vdr/04_isolation_report.md`
for the full analysis and replacement path.

**Fix:** Rewrite `shared/audit_trail/merkle_batch.py` using stdlib `hashlib`
(~50 lines). Eliminates the only GPL dependency.

---

### D2: cryptography package CVEs

**Severity:** Medium (see CVE report)
**Status:** Open — upgrade required

The `cryptography` package (3.4.8) has known CVEs. Upgrading to the latest
version resolves these.

**Fix:** `pip install --upgrade cryptography` and rebuild Docker images.

---

## Roadmap Items (Planned Steps)

The following roadmap steps remain for a complete, production-ready platform:

| Step | Description | Priority |
|------|-------------|---------|
| Step 5 | Live Alpaca order routing (paper → live) | High |
| Step 7 | RL agent for dynamic conviction thresholds | Medium |
| Step 8 | Multi-leg options strategies | Medium |
| Step 10 | Backtesting engine (VectorBT) | Medium |
| Step 22 | Tax lot optimization | Low |
| Step 25 | Earnings calendar integration | Medium |

All incomplete steps are tracked in `scripts/generate_docs.py` (ROADMAP_STEPS list).
