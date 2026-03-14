# Known Issues and Technical Debt

This register is maintained transparently so buyers can assess remaining work.
Issues are classified by severity: **Low**, **Medium**, **High**.

Last updated: March 2026

---

## Code Issues (C-series)

### C1: Dead Orchestrator Publish Path

**Severity:** Low
**Status:** Open
**Affects:** Paper trading — no functional impact

The orchestrator has a signal publish code path that routes to a dead subscriber.
The EMS receives signals via a different channel (working correctly). The dead path
is a holdover from an earlier architecture iteration.

**Fix:** Remove the dead publish call in `agents/brain.py`. No trading logic changes
required.

---

### C2: CIO Debate Hardcoded

**Severity:** Low
**Status:** Open — planned fix in Step 7 (RL agent)

The "Chief Investment Officer" debate function in the orchestrator uses hardcoded
conviction thresholds rather than a learned policy.

**Fix:** Step 7 (Reinforcement Learning Agent) will replace hardcoded thresholds
with a PPO-trained policy that adapts to market conditions.

---

### C3: macOS-only Kalshi Certificate Path

**Severity:** Medium
**Status:** Open

`Kalshi by Cemini/kalshi.py` contains a hardcoded macOS path for the TLS
certificate (`/Users/.../kalshi.pem`). On Linux/server, this requires a manual
edit.

**Fix:** Replace with `os.environ.get("KALSHI_CERT_PATH", "kalshi.pem")`. One-line
change, no logic impact.

---

### C6: Hardcoded Buying Power ($1,000)

**Severity:** Medium
**Status:** Open — paper trading only

`get_buying_power()` in the EMS returns a hardcoded $1,000 rather than querying
the live Alpaca balance. This is intentional during paper trading (prevents
accidental live orders above $1,000).

**Fix:** Add `LIVE_TRADING=true` environment variable check. When set, query
Alpaca `/account` endpoint for real buying power. When unset (default), return
configured paper trading limit.

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
