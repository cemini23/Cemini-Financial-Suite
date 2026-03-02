# Cemini Financial Suite

![Multi-Architecture Ready](https://img.shields.io/badge/Multi--Architecture-amd64%20%7C%20arm64-blue)
![Cross-Platform](https://img.shields.io/badge/Cross--Platform-Windows%20%7C%20Linux%20%7C%20macOS-green)

The **Cemini Financial Suite** is a private-use algorithmic trading platform built on a modular, Dockerized architecture. It integrates real-time market data ingestion, AI-driven signal generation, multi-broker execution, and a risk-gated trading playbook into a single deployable stack.

**Current phase:** Data accumulation / paper mode. No live equity or crypto orders are placed. Kalshi prediction market activity is active. All broker adapters default to paper mode.

**Three cooperating engines sharing intelligence via Redis pub/sub:**
- **Brain (LangGraph):** Orchestrator + EMS signal router. Reads regime and playbook intel from Redis before forwarding any trade signal.
- **QuantOS:** Stock/crypto engine (FastAPI, port 8001). RSI + FinBERT sentiment + BigQuery signal detection.
- **Kalshi by Cemini:** Prediction market engine (FastAPI, port 8000). BTC TA, Fed rate analysis, weather/social/Musk modules.

---

## 🚀 Installation Guide

### Prerequisites

Install these tools before anything else:

| Tool | Version | Download |
| :--- | :--- | :--- |
| **Git** | Latest | [git-scm.com](https://git-scm.com/downloads) |
| **Python** | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Docker Desktop** | Latest | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |

> **Windows users:** Enable WSL2 in Docker Desktop settings. When installing Python, check **"Add Python to PATH"**.

---

### Quick Setup (Recommended)

Clone the repo, then run the setup script for your platform — it handles venv creation, dependency install, and `.env` copying automatically.

**Mac / Linux**
```bash
git clone https://github.com/cemini23/Cemini-Financial-Suite.git
cd Cemini-Financial-Suite
./setup.sh
```

**Windows (Command Prompt or double-click)**
```bat
git clone https://github.com/cemini23/Cemini-Financial-Suite.git
cd Cemini-Financial-Suite
setup.bat
```

Both scripts will print `Setup complete! Edit .env with your API keys then run: docker compose up -d` when finished.

---

### Step 1 — Configure Environment Variables

Open `.env` in any text editor and fill in your credentials:

```
# Minimum required to start:
APCA_API_KEY_ID=your_alpaca_key
APCA_API_SECRET_KEY=your_alpaca_secret
POLYGON_API_KEY=your_polygon_key
DISCORD_WEBHOOK_URL=your_discord_webhook   # optional but recommended

# Infrastructure (defaults are set in docker-compose.yml, override here if needed):
REDIS_PASSWORD=cemini_redis_2026
POSTGRES_PASSWORD=quest
```

> The `.env` file is in `.gitignore` and will never be committed. Keep your secrets local.

---

### Step 2 — Launch the Full Stack

```bash
docker compose up -d --build
```

This starts all services defined in `docker-compose.yml`:

| Service | Internal Port | Exposed Via |
| :--- | :--- | :--- |
| **TimescaleDB (PostgreSQL)** | 5432 | Internal only |
| **pgAdmin** | 80 | nginx reverse proxy |
| **Redis** | 6379 | Internal only (password-protected) |
| **Deephaven UI** | 10000 | nginx reverse proxy |
| **Grafana** | 3000 | nginx reverse proxy |
| **Cemini OS (Streamlit)** | 8501 | nginx reverse proxy |
| **nginx** | 80 | `localhost:80` (or Cloudflare tunnel) |

> All internal services are isolated in the Docker network. External access is routed through **nginx** on port 80, optionally tunneled via **Cloudflare Zero Trust** (no open firewall ports required).

> **Redis requires a password.** The default is `cemini_redis_2026`, set via `REDIS_PASSWORD` in your `.env`. Never expose port 6379 publicly.

---

### Step 3 — Verify the Stack is Running

```bash
docker compose ps
```

All 18 active services should show `Up`. If you've pulled a code update, restart to apply changes:

```bash
docker compose down && docker compose up --build -d
```

Then run the sanity check:

```bash
python scripts/sanity_test.py
```

Expected output:
```
✅ SUCCESS: Test signal sent.
```

---

### Manual Setup (Alternative to setup scripts)

<details>
<summary>Expand for step-by-step manual instructions</summary>

**Create a virtual environment:**

| Mac / Linux | Windows |
| :--- | :--- |
| `python3 -m venv .venv` | `python -m venv venv` |
| `source .venv/bin/activate` | `venv\Scripts\activate` |

> Windows PowerShell only: if activation is blocked, first run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** `torch` and `transformers` are large packages (~2–4 GB). If you only need the Docker stack (recommended for servers), you can skip them by commenting them out in `requirements.txt`.

**Copy the env file:**

| Mac / Linux | Windows |
| :--- | :--- |
| `cp .env.example .env` | `copy .env.example .env` |

</details>

---

## 🛠️ Common Errors

| Error | Fix |
| :--- | :--- |
| `ModuleNotFoundError: No module named 'X'` | Your venv is not active. Run `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\Activate.ps1` (Windows) |
| `docker: command not found` | Docker Desktop is not installed or not running. Download from [docker.com](https://www.docker.com/products/docker-desktop/) |
| `Port 8501 is already in use` | Stop the conflicting process: `lsof -i :8501` (Mac/Linux) or `netstat -ano \| findstr :8501` (Windows) |
| `Connection refused` (database) | Wait 30 seconds after `docker compose up` — TimescaleDB takes time to initialize |
| `WRONGPASS` or `NOAUTH` (Redis) | Your `REDIS_PASSWORD` in `.env` doesn't match the one in `docker-compose.yml`. Default is `cemini_redis_2026` |
| `python3: command not found` (Windows) | Use `python` instead of `python3` on Windows |
| `Permission denied` (venv activate, Windows) | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell as Administrator |

---

## 🏗️ Architecture: "The Body"

The suite is designed as a modular organism, where each service plays a critical role. Because it leverages Docker, Redis, and standard PostgreSQL wire protocols, it runs seamlessly on **Windows (WSL2), Linux Servers, Intel Macs, and Apple Silicon (M-series)**.

- **Memory (TimescaleDB):** A time-series-optimized PostgreSQL database for market ticks and audit logs. Internal port `5432`.
- **Nervous System (Redis):** The authenticated, password-protected message bus facilitating communication between all subsystems. Internal port `6379`. Also hosts the **Intel Bus** (`intel:*` key namespace) for cross-system AI signal sharing.
- **Intel Bus (`core/intel_bus.py`):** A shared Redis-backed intelligence layer. QuantOS publishes market regime signals (`intel:vix_level`, `intel:spy_trend`, `intel:portfolio_heat`, `intel:btc_volume_spike`). Kalshi by Cemini publishes sentiment signals (`intel:btc_sentiment`, `intel:fed_bias`, `intel:social_score`, `intel:weather_edge`). The playbook_runner publishes `intel:playbook_snapshot` — regime + signal + risk state every 5 min. Both systems read from each other — no HTTP calls between containers.
- **Eyes (Ingestor):** Polls real-time market data via the Polygon.io REST API. Ingests 23 equity/ETF symbols during market hours and 7 crypto symbols 24/7, writing 1-min OHLCV ticks directly into TimescaleDB.
- **Brain (Analyst Swarm):** A LangGraph-orchestrated AI that analyzes market sentiment, technicals, and fundamentals to generate trade signals. Applies the **Regime Gate** — BUY signals are blocked before reaching the EMS when the playbook reports YELLOW or RED macro regime.
- **Hands (EMS):** The Execution Management System. Multi-broker adapter architecture: Kalshi (prediction market contracts via REST API v2, active), Robinhood (equities + options via robin_stocks, paper mode default), Alpaca (equities via official API, paper mode default).
- **Trading Playbook:** Observation-only layer running every 5 minutes. Classifies macro regime (GREEN/YELLOW/RED) based on SPY vs EMA21/SMA50 with JNK/TLT credit cross-validation. Runs 6 tactical signal detectors (EpisodicPivot, MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212). Computes risk metrics (fractional Kelly, CVaR, drawdown). Logs to Postgres + JSONL for future RL training. Does NOT place orders.
- **Kill Switch:** Monitors PnL velocity, order rates, latency, and price deviations. Broadcasts `CANCEL_ALL` on Redis `emergency_stop` channel — all broker adapters are subscribed.
- **Rover Scanner:** Paginates all open Kalshi prediction markets every 15 minutes, categorizes them by domain (weather / crypto / economics / politics), and publishes intel to Redis.
- **GDELT Harvester:** Ingests geopolitical event data from the GDELT Project every 15 minutes. Publishes a 0–100 risk score, per-region risk breakdown, and top-5 high-impact events to `intel:geopolitical_risk`, `intel:regional_risk`, and `intel:conflict_events`.
- **Face (Frontend UI):** A real-time dashboard (Deephaven + Streamlit via Cemini OS) and Grafana for metrics visualization.
- **Perimeter (nginx + Cloudflare):** nginx reverse proxy on port 80 routes all traffic. Cloudflare Zero Trust tunnel provides secure public access without opening firewall ports.

---

## 📋 Trading Playbook

The Trading Playbook (`trading_playbook/`) is an **observation-only layer** — it runs every 5 minutes, logs everything for future RL training, and publishes regime/signal state to Redis. It does **not** place orders.

### Macro Regime Classification (`macro_regime.py`)

| Regime | Condition | System Posture |
|--------|-----------|----------------|
| 🟢 GREEN | SPY > rising EMA21, JNK/TLT credit spread healthy | Normal operation — all signals pass regime gate |
| 🟡 YELLOW | SPY < EMA21 but > SMA50, credit stress detected | Defensive — BUY signals blocked at regime gate |
| 🔴 RED | SPY < SMA50, credit spread blowing out | Survival — cash/short only, all buys blocked |

The regime gate in `agents/orchestrator.py` blocks all BUY signals forwarded to the EMS when regime is YELLOW or RED.

### Signal Detectors (`signal_catalog.py`)

| Detector | Description |
|----------|-------------|
| **EpisodicPivot** | Massive volume + gap on earnings/news catalyst |
| **MomentumBurst** | Sustained directional move with expanding volume |
| **ElephantBar** | Single outsized candle with full-range close |
| **VCP** | Volatility Contraction Pattern — coil before breakout |
| **HighTightFlag** | Post-spike tight consolidation, institutional accumulation |
| **InsideBar212** | 2-candle inside bar with 12% thrust — gap-and-go setup |

### Risk Engine (`risk_engine.py`)

- **Fractional Kelly:** Position sizing at 25% of full Kelly (caps single-trade risk)
- **CVaR:** 99th-percentile conditional Value-at-Risk computed per position
- **DrawdownMonitor:** Tracks portfolio-level drawdown; escalates to YELLOW/RED posture

### Kill Switch (`kill_switch.py`)

Monitors four trip wires. Any breach broadcasts `CANCEL_ALL` on Redis `emergency_stop`:
- PnL velocity (losses accelerating beyond threshold)
- Order rate (orders-per-minute spike)
- Latency (broker round-trip exceeds SLA)
- Price deviation (fill price diverges from signal price)

---

## 🗄️ Data Pipeline

All market data flows through Polygon.io REST API → TimescaleDB. No WebSocket streaming — polling at configured intervals keeps costs predictable.

| Table | Source | Cadence | Content |
|-------|--------|---------|---------|
| `raw_market_ticks` | Polygon.io REST | 1-min | 1-min OHLCV for 23 equities + 7 crypto symbols |
| `macro_logs` | Alternative.me + FRED | 5-min | Fear & Greed Index + 10Y Treasury yield |
| `sentiment_logs` | X API (real data only) | On-demand | Social sentiment; mock mode permanently disabled |
| `playbook_logs` | playbook_runner | 5-min | Regime + signal + risk snapshot (JSONB) |
| `trade_history` | EMS / broker adapters | On-trade | Clean post-regime-gate trade records (since Feb 25, 2026) |
| `ai_trade_logs` | Brain / LangGraph | On-signal | AI signal decisions with reasoning |
| `gdelt_events` | GDELT Project | 15-min | ELEVATED+ geopolitical events |

**Equity symbols (23):** SPY, QQQ, IWM, DIA, AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AMD, AVGO, SMCI, ARM, PLTR, CRWD, DDOG, SNOW, COIN, MSTR, IBIT, ARKK

**Crypto symbols (7):** BTC/USD, ETH/USD, SOL/USD, BNB/USD, XRP/USD, DOGE/USD, ADA/USD

> **Data quarantine:** Pre-regime-gate data collected before Feb 25, 2026 is archived at `/opt/cemini/archives/data_quarantine/` and is not used for analysis or RL training.

---

## 🔄 CI/CD Pipeline

Every push to `main` runs the full gate sequence. All gates must be green before deployment:

```
lint (flake8) → pip-audit → bandit → TruffleHog → SSH deploy + auto-docs
                                                         ↕ (parallel)
                                                    update-docs job
```

| Gate | Tool | What it checks |
|------|------|----------------|
| **lint** | flake8 (max-line-length=120) | Syntax errors (E999), undefined names (F821), ambiguous variable names (E741) |
| **pip-audit** | pip-audit | CVE vulnerabilities in all pinned dependencies |
| **bandit** | bandit (SAST) | Security anti-patterns in Python source |
| **TruffleHog** | trufflehog | Secrets and credentials accidentally committed |
| **deploy** | SSH + docker compose | Pulls latest, rebuilds changed images, restarts services |
| **update-docs** | generate_docs.py | Refreshes AUTO: markers in README files, commits `[skip ci]` |

The `update-docs` job runs in parallel with `audit-and-deploy` — doc failures are informational only and never block deployment.

---

## 🛠️ Components & Ports

<!-- AUTO:SERVICES_TABLE -->
**19 active containers** (1 disabled)

| Container | Image/Build | Ports | Notes |
|-----------|-------------|-------|-------|
| `postgres` | timescale/timescaledb:latest-pg16 | 5432 | THE HEART (Data Storage) |
| `pgadmin` | dpage/pgadmin4 | 80 |  |
| `redis` | redis:7-alpine | 6379 | THE SPINAL CORD (Messaging) |
| `polygon_ingestor` | (build: Dockerfile.ingestor) | internal | NODE 1: PERCEPTION (Ingestion) |
| `brain` | (build: Dockerfile.brain) | internal | NODE 2-4: THE BRAIN (Intelligence) |
| `scribe_logger` | (build: Dockerfile.logger) | internal | THE SCRIBE (Logging) |
| `coach_analyzer` | (build: Dockerfile.analyzer) | internal | THE COACH (Analysis) |
| `social_scraper` | (build: Dockerfile.scraper) | internal | SCRAPERS (Intelligence) |
| `macro_scraper` | (build: Dockerfile.scraper) | internal |  |
| `gdelt_harvester` | (build: Dockerfile.scraper) | internal | intel:conflict_events / intel:regional_risk, logs ELEVATED+ events to Postgres. |
| `kalshi_autopilot` | (build: Dockerfile.autopilot) | internal | social_alpha, musk_monitor — all in paper mode by default. |
| `rover_scanner` | (build: Dockerfile.autopilot) | internal | (weather / crypto / economics / politics), and publishes intel to Redis. |
| `ems_executor` | (build: Dockerfile.ems) | internal | NODE 5: THE SWORD (Execution) |
| `cemini_os` | (build: Dockerfile.ui) | 8501 | CEMINI OS (Streamlit Dashboard) |
| `deephaven` | ghcr.io/deephaven/server:latest | 10000 | THE VISUAL NERVOUS SYSTEM (Telemetry) |
| `grafana_viz` | grafana/grafana:latest | 3000 |  |
| `cemini_proxy` | nginx:alpine | 80 | PERIMETER DEFENSE |
| `cloudflare_tunnel` | cloudflare/cloudflared:latest | internal |  |
| `playbook_runner` | (build: Dockerfile.playbook) | internal | future RL model.  Does NOT place orders.  Harvesters are unaffected. |

**Disabled (profile-gated):** `signal_generator`
<!-- /AUTO:SERVICES_TABLE -->

---

## 🔮 Broker Adapters

All adapters implement a common `BrokerInterface`. The router in `ems/` dispatches by signal type and time-of-day availability. All adapters default to paper mode — live trading requires explicit `.env` flag.

<!-- AUTO:BROKER_STATUS -->
| Broker | Status | API | Default Mode |
|--------|--------|-----|--------------|
| Kalshi | Active | REST API v2 (RSA-signed) | Paper default |
| Robinhood | Integrated | robin_stocks (unofficial) | Paper default |
| Alpaca | Integrated | Official REST API | Paper default |
| IBKR | Planned | TWS API / FIX CTCI | Requires LLC + LEI |
<!-- /AUTO:BROKER_STATUS -->

---

## 📡 Intel Bus (Redis)

All inter-service communication uses Redis pub/sub and key-value. No direct HTTP calls between containers.

<!-- AUTO:REDIS_CHANNELS -->
| Key | Publisher | Description |
|-----|-----------|-------------|
| `trade_signals` | various | brain → EMS (trade execution commands) |
| `emergency_stop` | various | Kill switch CANCEL_ALL broadcast |
| `strategy_mode` | various | analyzer → conservative | aggressive | sniper |
| `intel:btc_spy_corr` | various | BTC/SPY 30-day rolling correlation float |
| `intel:playbook_snapshot` | various | playbook_runner: regime + signal + risk state (every 5 min) |
| `intel:spy_trend` | various | SPY trend direction from playbook_runner |
| `intel:geopolitical_risk` | various | GDELT: 0-100 risk score, level, top event (every 15 min) |
| `intel:conflict_events` | various | GDELT: top-5 high-impact events JSON list |
| `intel:regional_risk` | various | GDELT: per-region risk scores (asia_pacific, middle_east, europe, americas) |
| `macro:fear_greed` | various | Fear & Greed Index (macro_scraper, every 5 min) |
<!-- /AUTO:REDIS_CHANNELS -->

---

## 🗺️ Development Roadmap

<!-- AUTO:ROADMAP_STATUS -->
**Progress: 5/14 steps complete (35%)**

| Step | Name | Status |
|------|------|--------|
| 1 | CI/CD Hardening | ✅ Complete (Feb 28, 2026) |
| 2 | Docker Network Segmentation | ✅ Complete (Mar 1, 2026) |
| 3 | Performance Dashboard | ⬜ Pending |
| 4 | Kalshi Rewards Scanner | ⬜ Pending |
| 5 | X/Twitter Thread Tool | ⬜ Pending |
| 6 | Equity Tick Data | ✅ Complete (Feb 26, 2026) |
| 7 | RL Training Loop | ⬜ Pending |
| 8 | Backtesting in CI/CD | ⬜ Pending |
| 9 | Options Strategies | ⬜ Pending |
| 10 | Live Trading Integration | ⬜ Pending |
| 11 | Shadow Testing Infra | ⬜ Pending |
| 12 | Copy Trading / Signals | ~~Removed~~ |
| 13 | Arbitrage Scanner | ⬜ Pending |
| 14 | GDELT Geopolitical Intel | ✅ Complete (Mar 1, 2026) |
| 15 | Auto-Documentation CI | ✅ Complete (Mar 1, 2026) |
<!-- /AUTO:ROADMAP_STATUS -->

---

## 🔬 Test & Security Status

<!-- AUTO:TEST_SUMMARY -->
**Tests:** 51 passing
**pip-audit:** not available locally (check CI)
**bandit (SAST):** see CI
**CI gates:** lint → pip-audit → bandit → TruffleHog → deploy (all required)
<!-- /AUTO:TEST_SUMMARY -->

---

<!-- AUTO:LAST_UPDATED -->
*Auto-generated: 2026-03-02 02:17 UTC*
<!-- /AUTO:LAST_UPDATED -->

**Copyright (c) 2026 Cemini23 / Claudio Barone Jr.**
