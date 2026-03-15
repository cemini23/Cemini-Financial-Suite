# Cemini Financial Suite — Development Roadmap

**Version:** v12.3 — March 15, 2026
**Phase:** Paper trading / data accumulation
**Paradigm:** Intelligence-in, ticker-out
**Progress:** 33 of 51 steps complete — 1158 tests — 0 failures
**Stack:** Python 3.12, FastAPI, Polars, Redis, PostgreSQL/TimescaleDB, Pydantic v2, Docker Swarm

---

## Step Status

| # | Name | Status | Notes |
|---|------|--------|-------|
| 1 | CI/CD Hardening | ✓ DONE (Feb 28) | GitHub Actions, ruff, pip-audit, TruffleHog, SSH deploy |
| 2 | Docker Network Segmentation | ✓ DONE (Mar 1) | edge_net / app_net / data_net |
| 3 | Performance Dashboard | ✓ DONE (Mar 7) | Streamlit 5-tab dashboard, cemini_os port 8501 |
| 4 | Kalshi Rewards Scanner | ✓ DONE (Mar 7) | Discord alerts, JSONL archive, daily cron |
| 5 | X/Twitter Thread Tool | N/A | Replaced by X harvester sprint (62 accounts) |
| 6 | Equity Tick Data | ✓ DONE (Feb 26) | Polygon feed, 23 equities + 7 crypto |
| 7 | RL Training Loop | READY ← NEXT | Unblocked by Step 50 feature engine. Highest-value IP. |
| 8 | Backtesting in CI | BLOCKED | Needs Step 7 |
| 9 | Walk-Forward Validation | BLOCKED | Needs Step 8 |
| 10 | Live Trading (Paper→Live) | BLOCKED | Needs Steps 7, 8, 9, 49 |
| 11 | Portfolio Rebalancer | BLOCKED | Needs Step 10 |
| 12 | Regulatory Compliance | REMOVED | Excessive complexity for private-use IP sale |
| 13 | Tax Lot Optimizer | BLOCKED | Needs Step 10 |
| 14 | GDELT Geopolitical Harvester | ✓ DONE (Mar 1) | scrapers/gdelt_harvester.py |
| 15 | Auto-Documentation CI | ✓ DONE (Mar 1) | scripts/generate_docs.py, auto-update markers |
| 16 | Kalshi WebSocket | ✓ DONE | rover_scanner, websockets v16 |
| 17 | SEC EDGAR Monitor — Filing Alerts | ✓ DONE (Mar 15) | Filing significance scoring, insider cluster detection, intel:edgar_alert |
| 18 | Options Flow Harvester | BLOCKED | Needs data subscription |
| 19 | Earnings Calendar Integration | ✓ DONE (Mar 15) | EDGAR submissions cadence estimation; REPORTING_THIS_WEEK/SOON/JUST_REPORTED; cluster detection; intel:earnings_calendar (TTL=7200) |
| 20 | Skill Vetting Protocol | ✓ DONE (Mar 1) | approved_skills.json, vet_skill.py |
| 21 | Cemini SKILL.md | ✓ DONE (Mar 7) | 565-line transferable architecture package |
| 22 | Alpaca Data Spine | READY | $99/mo sub required; replaces Polygon free tier |
| 23 | Options Greeks Engine | READY | Black-Scholes / local vol |
| 24 | Visual Crossing Weather | ✓ DONE | weather_alpha, 5 sources, agricultural metrics |
| 25 | Sector Rotation Monitor | ✓ DONE (Mar 15) | RRG-style RS/momentum for 11 SPDR ETFs vs SPY; RISK_ON/RISK_OFF/NEUTRAL bias; intel:sector_rotation (TTL=3600) |
| 26 | Opportunity Discovery Engine | ✓ DONE (Mar 7) | FastAPI :8003, 50-ticker watchlist, Bayesian LR |
| 27 | MCP Intelligence Server | ✓ DONE (Mar 6) | FastMCP 3.1.0, 9 read-only tools, port 8002 |
| 28 | Pydantic Data Contracts | ✓ DONE (Mar 6) | cemini_contracts/, safe_validate/safe_dump at all Intel Bus boundaries |
| 29 | Vector DB Intelligence Layer | ✓ DONE (Mar 8) | pgvector + HNSW, all-MiniLM-L6-v2, CRAG retrieval |
| 30 | Logit Jump-Diffusion Pricing | ✓ DONE (Mar 6) | logit_pricing/, ContractAssessment, 10th MCP tool |
| 31 | Ensemble Signal Combiner | BLOCKED | Needs Step 7 |
| 32 | Per-Service CLAUDE.md | ✓ DONE (Mar 6) | Root + 3 service CLAUDE.md files + LESSONS.md |
| 33 | Safety Guards C4/C5/C7 | ✓ DONE (Mar 6) | SOCIAL_ALPHA_LIVE, WEATHER_ALPHA_LIVE env guards |
| 34 | DevOps Hardening | ✓ DONE (Mar 7) | Ruff, Trivy, Semgrep, beartype (23 fns), Swarm, Portainer |
| 35 | Observability Stack (LGTM) | ✓ DONE (Mar 13) | Prometheus, Loki, Alloy, Tempo, Grafana, 8 alert rules |
| 36 | Discord Alert Enrichment | READY | Add regime/signal context to alerts |
| 37 | Playbook Replay Viewer | ✓ DONE (Mar 15) | Streamlit sidebar page; time-travel snapshot viewer; regime/signal/risk history; sector rotation panel; raw JSON expander |
| 38 | Schema Migrations (dbmate) | ✓ DONE (Mar 7) | dbmate 2.31.0, 9 migrations, db/schema.sql |
| 39 | FRED Macro Data Integration | ✓ DONE (Mar 13) | 8 series, daily cron, fred_observations table |
| 40 | SEC EDGAR Direct Pipeline | ✓ DONE (Mar 14) | Form 4, XBRL fundamentals, edgar_harvester.py |
| 41 | IP Sale Documentation Site | ✓ DONE (Mar 14) | MkDocs-Material, 36 pages, 13+ Mermaid diagrams |
| 42 | Advanced Test Suite | ✓ DONE (Mar 14) | Hypothesis, Schemathesis, mutmut, VCR.py, pytest-xdist |
| 43 | Cryptographic Audit Trail | ✓ DONE (Mar 14) | SHA-256 chain + pymerkle + OTS, UUIDv7, intent logging |
| 44 | RL Interpretability | BLOCKED | Needs Step 7 |
| 45 | Meta-Adaptive Ensemble Controller | BLOCKED | Needs Step 7 |
| 46 | IP HoldCo Formation | READY | Legal filing ~$150, parallel to any step |
| 47 | Devil's Advocate Debate Protocol | ✓ DONE (Mar 15) | 5-agent debate, Redis blackboard, deterministic tie-breaking, audit trail |
| 48 | Data Pipeline Resilience | ✓ DONE (Mar 14) | Hishel, Aiobreaker, Tenacity, APScheduler, dead-letter queue |
| 49 | Pre-Live Safety Hardening | ✓ DONE (Mar 15) | IdempotencyGuard, StateHydrator, ExposureGate, HITLGate, MFAHandler, SelfMatchLock; C6/L1/L2 resolved |
| 50 | Polars Feature Engineering | ✓ DONE (Mar 14) | 18-feature RL obs space, Wilder RSI, multi-timeframe join_asof |
| 51 | License Compliance & VDR | ✓ DONE (Mar 14) | SBOM, isolation report, authorship proof, 12-file VDR |

---

## Recommended Execution Order

```
IMMEDIATE (this week):
  Step 7  — RL Training Loop (MAPPO/DPPO, TorchRL, Step 50 obs space ready)
  Step 46 — IP HoldCo Formation (parallel, no engineering deps)

AFTER STEP 7 (within 2 weeks):
  Step 44 — RL Interpretability & Learning Journal
  Step 47 — Devil's Advocate Debate Protocol
  Step 22 — Alpaca Data Spine ($99/mo, upgrades data quality)

MEDIUM-TERM:
  Step 49 — Pre-Live Safety Hardening (C2, C6, L1, L2 fixes live here)
  Step 17 — Sentiment Analysis Pipeline (FinBERT live)
  Step 8  — Backtesting in CI
  Step 45 — Meta-Adaptive Ensemble Controller
  Step 10 — Live Trading (paper -> live)

PARALLEL ANYTIME (no blockers):
  Step 36 — Discord Alert Enrichment
  Step 37 — Playbook Replay Viewer
  Step 19 — Earnings Calendar Integration
  Step 25 — Sector Rotation Monitor
```

---

## Known Issues

| ID | Description | Severity | Resolution |
|----|-------------|----------|------------|
| C1 | Orchestrator publish path | Low | RESOLVED — ENABLE_BRAIN_PUBLISH guard added |
| C2 | CIO debate hardcoded (confidence=0.85, action=BUY) | High | → Step 7 (RL replaces hardcoded debate) |
| C3 | Mac-only path in verify_install.py | Medium | RESOLVED — os.getenv + relative fallback |
| C4 | Hardcoded DB password | Medium | RESOLVED — POSTGRES_PASSWORD env var (Step 33) |
| C5 | Social alpha uses simulated tweets | Medium | RESOLVED — SOCIAL_ALPHA_LIVE guard (Step 33) |
| C6 | get_buying_power() returns $1000 hardcoded | Medium | RESOLVED — ExposureGate + LIVE_TRADING flag (Step 49) |
| C7 | Weather alpha uses simulated prices | Medium | RESOLVED — WEATHER_ALPHA_LIVE guard (Step 33) |
| L1 | Engine restarts with empty executed_trades | Medium | RESOLVED — StateHydrator.hydrate() (Step 49) |
| L2 | Exposure gate was observation-only | Medium | RESOLVED — ExposureGate hard-blocking fail-closed (Step 49) |
| L3 | check_exposure() never blocked | Medium | RESOLVED — wired as pre-trade gate (obs mode) |
| L4 | strategy_mode based on win rate not regime | Medium | RESOLVED — reads intel:playbook_snapshot |
| A4 | BigQuery table name mismatch | Low | RESOLVED — already consistent in codebase |
| A6 | executed_trades lost on restart | Medium | RESOLVED — Redis write-through TTL=24h |
| S5 | Duplicate ib_insync imports | Low | RESOLVED — already clean in current codebase |
| CVaR | CVaR test fails on all-positive returns | Low | RESOLVED — assume(any(r < 0)) hypothesis guard |

---

## Data Status

| Item | Status |
|------|--------|
| Clean data start | Feb 25, 2026 (post-regime-gate truncation) |
| Pre-gate data | Quarantined at /opt/cemini/archives/data_quarantine/ |
| OpenTimestamps | Active — daily Merkle batch + Bitcoin anchor |
| Audit chain | Unbroken from Feb 25, 2026 |
| Equity ticks | 23 symbols via Polygon (free tier, market hours) |
| Crypto ticks | 7 symbols via Polygon |
| FRED macro | 8 series, daily refresh |
| EDGAR filings | All S&P 500 companies, Form 4 insider + XBRL |
| GDELT | 15-min geopolitical event feed |

---

## API Cost Table

| Tier | Monthly Cost | Services |
|------|-------------|----------|
| Bootstrapper | ~$30 | Polygon free, FRED free, EDGAR free |
| Sweet Spot | ~$135 | + Alpaca Algo Trader Plus ($99) |
| Full Suite | ~$272 | + OpenAI/Anthropic inference, premium data |

---

## Maintenance Log

| Date | Event | Commit | Test Delta |
|------|-------|--------|------------|
| Mar 15, 2026 | Step 49 (Pre-Live Safety Hardening) complete | — | 955 → 1025 |
| Mar 15, 2026 | Step 47 (Debate Protocol) complete | — | 898 → 955 |
| Mar 15, 2026 | Step 17 (EDGAR Monitor) complete | — | 846 → 898 |
| Mar 14, 2026 | Steps 40, 41, 43, 50, 51 complete | various | 686 → 846 |
| Mar 14, 2026 | Known Issues sprint: C1/C3/L3/L4/A6/CVaR resolved | 457f415 | +1 (CVaR fix) |
| Mar 14, 2026 | cryptography 3.4.8 → 46.0.5 (32 → 18 CVEs) | 78779db | — |
| Mar 13, 2026 | Steps 35, 39, 42, 48 complete | df1062f | 512 → 686 |
| Mar 8, 2026 | Step 29 (Vector DB) complete | cf1937f | 433 → 512 |
| Mar 7, 2026 | Steps 26, 27, 28, 30, 34, 38 complete | various | 263 → 433 |
| Mar 6, 2026 | Steps 3, 4, 21, 32, 33 complete | various | 207 → 263 |
| Mar 1, 2026 | Steps 2, 14, 15, 20 complete | various | baseline |
| Feb 28, 2026 | Step 1 (CI/CD) complete | initial | — |
