# Cemini Financial Suite

![Multi-Architecture Ready](https://img.shields.io/badge/Multi--Architecture-amd64%20%7C%20arm64-blue)
![Cross-Platform](https://img.shields.io/badge/Cross--Platform-Windows%20%7C%20Linux%20%7C%20macOS-green)

The **Cemini Financial Suite** is a **Universal, Cross-Platform Trading Architecture** designed for high-frequency financial operations. Built on a modular, Dockerized foundation, it integrates real-time market data, AI-driven decision-making, and institutional execution into a unified, hardware-agnostic environment.

---

## 🚀 Installation Guide

### Prerequisites

Install these tools before anything else:

| Tool | Version | Download |
| :--- | :--- | :--- |
| **Git** | Latest | [git-scm.com](https://git-scm.com/downloads) |
| **Python** | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Docker Desktop** | Latest | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |

> **Windows users:** Enable WSL2 in Docker Desktop settings. All commands below run in **PowerShell** unless noted.

---

### Step 1 — Clone the Repository

**Mac / Linux:**
```bash
git clone https://github.com/cemini23/Cemini-Financial-Suite.git
cd Cemini-Financial-Suite
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/cemini23/Cemini-Financial-Suite.git
cd Cemini-Financial-Suite
```

---

### Step 2 — Create a Virtual Environment

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

> If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

---

### Step 3 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** `torch` and `nautilus-trader` are large packages (~2–4 GB). If you only need the Docker stack (recommended), you can skip them:
> ```bash
> pip install -r requirements.txt --ignore-requires-python \
>   $(grep -v 'torch\|nautilus' requirements.txt | grep -v '^#' | tr '\n' ' ')
> ```

---

### Step 4 — Configure Environment Variables

**Mac / Linux:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
copy .env.example .env
```

Open `.env` in any text editor and fill in your credentials:

```
# Minimum required to start:
APCA_API_KEY_ID=your_alpaca_key
APCA_API_SECRET_KEY=your_alpaca_secret
POLYGON_API_KEY=your_polygon_key
DISCORD_WEBHOOK_URL=your_discord_webhook   # optional but recommended
```

> The `.env` file is in `.gitignore` and will never be committed. Keep your secrets local.

---

### Step 5 — Launch the Full Stack

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

### Step 6 — Verify the Stack is Running

```bash
docker compose ps
```

All services should show `Up`. If you've pulled a code update, restart to apply changes:

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

-   **Memory (TimescaleDB):** A time-series-optimized PostgreSQL database (TimescaleDB) for market ticks and audit logs. Internal port `5432`.
-   **Nervous System (Redis):** The authenticated, password-protected message bus facilitating communication between all subsystems. Internal port `6379`. Also hosts the **Intel Bus** (`intel:*` key namespace) for cross-system AI signal sharing.
-   **Intel Bus (`core/intel_bus.py`):** A shared Redis-backed intelligence layer. QuantOS publishes market regime signals (`intel:vix_level`, `intel:spy_trend`, `intel:portfolio_heat`, `intel:btc_volume_spike`). Kalshi by Cemini publishes sentiment signals (`intel:btc_sentiment`, `intel:fed_bias`, `intel:social_score`, `intel:weather_edge`). Both systems read from each other — no HTTP calls between containers.
-   **Eyes (Ingestor):** Streams real-time market data (via Polygon.io or Alpaca) directly into TimescaleDB.
-   **Brain (Analyst Swarm):** A LangGraph-orchestrated AI that analyzes market sentiment, technicals, and fundamentals to generate trades.
-   **Hands (EMS):** The Execution Management System, which handles brokerage adapters (Robinhood, Alpaca, Kalshi) to execute orders via the Redis bus.
-   **Face (Frontend UI):** A real-time dashboard (Deephaven + Streamlit via Cemini OS) and Grafana for metrics visualization.
-   **Perimeter (nginx + Cloudflare):** nginx reverse proxy on port 80 routes all traffic. Cloudflare Zero Trust tunnel provides secure public access without opening firewall ports.

---

## 🛠️ Components & Ports

| Service | Internal Port | Description |
| :--- | :--- | :--- |
| **TimescaleDB (PostgreSQL)** | 5432 | Time-series data storage & querying |
| **Redis** | 6379 | Messaging, pub/sub, and Intel Bus (password-protected) |
| **Deephaven UI** | 10000 | Advanced analytics dashboarding |
| **Cemini OS (Streamlit)** | 8501 | Real-time trading dashboard |
| **Grafana** | 3000 | Metrics & performance visualization |
| **nginx** | 80 | Reverse proxy (external entry point) |
| **Cloudflare Tunnel** | — | Zero Trust remote access (no open ports) |

---

## 🔮 Future Development

Our next phase of development focuses on:
-   **Live Mode Activation:** Intel Bus and all safety guards are in place. Live trading will be re-enabled after paper mode validation is complete.
-   **FinBERT News Pipeline:** Scaling the FinBERT news analysis module to feed higher-confidence catalyst data into the Master Strategy Matrix.
-   **Institutional Scaling:** Enhancing the FIX adapter for broader Prediction Market coverage across Kalshi contract categories.
-   **Backtesting Engine:** Leveraging TimescaleDB hypertables for historical replay and strategy validation against real tick data.

---

**Copyright (c) 2026 Cemini23 / Claudio Barone Jr.**
