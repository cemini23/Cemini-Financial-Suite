# Executive Summary — Cemini Financial Suite

**Classification:** Confidential — Prospective Buyer Use Only
**Date:** March 2026

---

## What Is Cemini?

Cemini Financial Suite is a **private-use algorithmic trading platform** built for
active trading across three asset classes: US equities, cryptocurrency, and prediction
markets (Kalshi). The platform is fully operational on a single Hetzner VPS
(Ubuntu 24, 4 vCPU, 16 GB RAM) running approximately 26 Docker containers.

The codebase represents roughly 18 months of focused development by a solo developer
and is offered for sale as a complete intellectual property package.

---

## What Does It Do?

The platform follows an **Intelligence-in / Ticker-out** paradigm:

1. **Intelligence gathering**: Six real-time data pipelines harvest market data,
   macro indicators (FRED), SEC filings (EDGAR), social sentiment, geopolitical signals
   (GDELT), and weather data.

2. **Signal generation**: Six pattern detectors analyze price action and generate
   buy/sell signals with conviction scores (Bayesian Logistic Regression).

3. **Regime classification**: A macro regime engine classifies market conditions
   as GREEN / YELLOW / RED (traffic-light model) and gates signal execution.

4. **Risk management**: Kelly Criterion position sizing, CVaR limits, and drawdown
   monitoring protect capital. A hardware kill switch sends CANCEL_ALL to all brokers.

5. **Execution**: An EMS routes orders to Alpaca (equities/crypto) and Kalshi
   (prediction markets). Currently in **paper trading mode** — no live capital at risk.

6. **Discovery**: An opportunity screener polls all intelligence channels every 30 seconds
   and maintains a dynamic 50-ticker watchlist for the signal engines.

---

## Architecture at a Glance

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Root Orchestrator | Python + Redis | Coordinates brain, analyzer, EMS |
| QuantOS | FastAPI :8001 | Equity/crypto signal engine |
| Kalshi by Cemini | FastAPI :8000 | Prediction market engine |
| Trading Playbook | APScheduler | Observation-only regime/signal log |
| Opportunity Screener | FastAPI :8003 | Real-time discovery engine |
| MCP Intelligence Server | FastMCP :8002 | 10 read-only tools for AI integration |
| Intelligence Layer | PostgreSQL + pgvector | CRAG semantic retrieval |
| Observability | Prometheus + Loki + Tempo + Grafana | Full LGTM stack |
| Database | PostgreSQL 16 + TimescaleDB | Time-series market data |
| Cache/Bus | Redis 7 | Pub/sub + intel namespace |

**Total services:** ~26 Docker containers
**Networks:** edge_net (nginx/cloudflare), app_net (services), data_net (postgres/redis)

---

## Current State

| Metric | Value |
|--------|-------|
| Roadmap steps completed | 25 of 51 |
| Test suite | 778+ passing, ~10 skipped |
| CI/CD pipeline | 6 stages (lint, pip-audit, trivy, semgrep, test, deploy) |
| Trading mode | Paper trading (no live capital at risk) |
| Uptime | Running since Feb 2026 |

---

## Quality Signals

**Cryptographic audit trail** (Step 43):
- Layer 1: SHA-256 hash chain — every trade is hashed and chained (immutable JSONL + PostgreSQL)
- Layer 2: Daily Merkle tree — daily commitment batches with Merkle root
- Layer 3: OpenTimestamps — Bitcoin blockchain anchoring for third-party verification

**Test coverage** (Step 42):
- 778+ passing tests across unit, property-based (Hypothesis), API fuzz (Schemathesis), mutation (mutmut)
- Parallel execution via pytest-xdist

**Security pipeline** (Step 34):
- Ruff (lint + security), Trivy (container/filesystem scan), Semgrep (custom trading rules)
- TruffleHog secret scanning on every commit

**Pydantic v2 data contracts** (Step 28):
- All Intel Bus read/write boundaries validated with Pydantic models
- Runtime type enforcement with @beartype on 23 critical functions

---

## Technology Stack

- **Language:** Python 3.12
- **APIs:** FastAPI + Uvicorn
- **Data validation:** Pydantic v2
- **Database:** PostgreSQL 16 + TimescaleDB + pgvector
- **Cache:** Redis 7 (pub/sub + persistence AOF)
- **Container:** Docker + Docker Swarm
- **Observability:** Prometheus, Loki, Tempo, Grafana (LGTM)
- **ML/Math:** NumPy, SciPy, Logit-space jump-diffusion pricing
- **Testing:** pytest, Hypothesis, Schemathesis, mutmut, VCR.py

---

## Revenue Model / Exit Strategy

This platform is offered as a **complete IP sale**. The buyer receives:

- Full Python source code (~40,000 lines across 300+ files)
- All architecture documentation (36-page MkDocs site)
- Complete virtual data room (this directory)
- Deployment instructions (Ubuntu 24 + Docker)
- API key rotation checklist (keys rotated pre-sale)

**What the buyer can do:**
- Continue paper trading → transition to live trading
- License signal generation to other traders
- Integrate with additional brokers (Interactive Brokers, TD Ameritrade)
- Extend the 51-step roadmap with remaining features

**What is NOT included:**
- Ongoing support or maintenance
- API keys for third-party services
- Historical trade data (quarantined for privacy)

---

## Contact

This VDR package was prepared by the sole developer. Contact via GitHub
(cemini23/Cemini-Financial-Suite) for transaction inquiries.
