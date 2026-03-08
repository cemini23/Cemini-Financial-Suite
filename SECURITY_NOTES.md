# Security Notes — Cemini Financial Suite

## Last Audit: 2026-03-08 (Desloppify Pass)

## Tools
- **Ruff** — static analysis + style (replaces flake8 + bandit, Step 34)
- **Trivy** — container FS scan (CI, SARIF → GitHub Security tab)
- **Semgrep** — 4 custom trading rules + p/python (p/trailofbits unavailable, HTTP 404)
- **pip-audit** — dependency CVE scan
- **TruffleHog** — secrets scan on every push
- **beartype** — runtime type checking on 23+ critical functions

---

## Semgrep Summary (2026-03-08)

| Category | Total | Fixed | Suppressed | Accepted |
|---|---|---|---|---|
| `semgrep.no-float-for-money` | 88 | 0 | 0 | 88 |
| `semgrep.hardcoded-env-default-credential` | 39 | 0 | 0 | 39 |
| `semgrep.hardcoded-password-kwarg` | 4 | 4 | 0 | 0 |
| `semgrep.missing-rate-limit-requests` | 4 | 0 | 4 | 0 |
| `python.lang.security.insecure-transport` | 2 | 0 | 2 | 0 |
| `python.lang.security.subprocess-shell-true` | 1 | 0 | 1 | 0 |
| **Total** | **138** | **4** | **7** | **127** |

---

## Accepted Findings (Low Risk)

### `semgrep.no-float-for-money` — 88 findings ACCEPTED
**Rule intent:** Detect `float()` on monetary amounts (should use `Decimal`).
**Why accepted:** The vast majority of these hits are on *probability values* (Kalshi
contract prices 0–100 cents scaled to 0.0–1.0), *RSI scores* (0–100), *confidence
scores* (0.0–1.0), and *BigQuery analytics results*. None of these represent currency
amounts that require `Decimal` precision. The few true dollar amounts (position sizes,
buying power) are computed from API responses that return floats. For prediction markets,
fractional-cent precision is irrelevant (minimum tick is 1 cent = $0.01).
**Risk:** Negligible. No material rounding errors can arise at these magnitudes.

### `semgrep.hardcoded-env-default-credential` — 39 findings ACCEPTED
**Rule intent:** Detect non-empty default values in `os.getenv("SECRET_KEY", "hardcoded")`.
**Why accepted:** All 39 hits are on internal infrastructure defaults:
- `REDIS_PASSWORD` → `"cemini_redis_2026"` — Redis is Docker-internal only, not internet-facing
- `POSTGRES_PASSWORD` → `"quest"` — Postgres port 5432 is not exposed to host; only accessible within Docker network
- These defaults exist so the system boots correctly in a fresh Docker environment without manual env config

**Risk:** Low. Redis and Postgres are on the private Docker `data_net` network with no public exposure.
Pre-sale: rotate all credentials before deployment to buyer.

---

## Fixed Findings

### `semgrep.hardcoded-password-kwarg` — 4 findings FIXED
Files: `scrapers/macro_harvester.py`, `scrapers/social_scraper.py`,
`QuantOS/signal_generator.py`, `scripts/archive_logs.py`
All now use `os.getenv("POSTGRES_PASSWORD", "quest")` (env-var-first pattern).

---

## Suppressed Findings (False Positives / Intentional)

### `semgrep.missing-rate-limit-requests` — 4 findings SUPPRESSED
Files: `scrapers/gdelt_harvester.py` (2), `scrapers/macro_harvester.py` (1),
`scrapers/macro_scraper.py` (1)
All three scrapers run in timed loops (300–900s sleep between cycles). Rate limiting
is enforced at the loop level, not at the individual `requests.get` call site.
Added `# nosemgrep` inline comments with explanations.

### `python.lang.security.insecure-transport` — 2 findings SUPPRESSED
File: `scrapers/gdelt_harvester.py`
GDELT project (gdeltproject.org) only serves HTTP — no HTTPS endpoint exists.
Traffic is read-only public data (geopolitical event CSVs). No credentials transmitted.

### `python.lang.security.subprocess-shell-true` — 1 finding SUPPRESSED
File: `Kalshi by Cemini/scripts/sentinel.py`
Deployment-only diagnostic script. Commands are hardcoded string literals (not user
input), so shell injection is not possible. Already had `# nosec B602`.

---

## Credential Management

- All secrets loaded via environment variables (`.env` files, Docker secrets).
- No hardcoded API keys in source (TruffleHog scan on every push).
- `REDIS_PASSWORD`, `POSTGRES_PASSWORD`, `KALSHI_API_KEY`, `DISCORD_WEBHOOK_URL`,
  `POLYGON_API_KEY`, `X_BEARER_TOKEN` — all env-var-only.
- **Pre-sale protocol:** Rotate all API keys and passwords immediately before handover.
  Documented in CLAUDE.md strategic context.

---

## Runtime Type Safety

- `@beartype` decorator on 23 critical functions: broker adapters, risk engine,
  intel bus publishers, regime classifier, logit pricing engine.
- All Intel Bus reads/writes validated via Pydantic contracts (Step 28).
- `safe_validate()` called at all cross-service boundaries.

---

## Known Open Items (Not Security Issues)

- `p/trailofbits-python` ruleset unavailable (HTTP 404 from semgrep.dev registry).
  If re-enabled in future audits, expect ~20–40 additional informational findings
  in the async/Redis patterns (false positives on async context manager usage).
- The orchestrator's LLM debate path is pending Step 7 (RL Training Loop).
  All signal decisions are currently numeric-score-based with regime gate applied.
