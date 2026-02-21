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

| Service | Port | URL |
| :--- | :--- | :--- |
| **QuestDB** | 9000 / 8812 | http://localhost:9000 |
| **Redis** | 6379 | — |
| **Deephaven UI** | 10000 | http://localhost:10000 |
| **FastAPI Backend** | 8000 | http://localhost:8000/docs |
| **Frontend Dashboard** | 8501 | http://localhost:8501 |

---

### Step 6 — Verify the Stack is Running

```bash
docker compose ps
```

All services should show `Up`. Then run the sanity check:

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
| `Connection refused` (database) | Wait 30 seconds after `docker compose up` — QuestDB takes time to initialize |
| `python3: command not found` (Windows) | Use `python` instead of `python3` on Windows |
| `Permission denied` (venv activate, Windows) | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell as Administrator |

---

## 🏗️ Architecture: "The Body"

The suite is designed as a modular organism, where each service plays a critical role. Because it leverages Docker, Redis, and standard PostgreSQL wire protocols, it runs seamlessly on **Windows (WSL2), Linux Servers, Intel Macs, and Apple Silicon (M-series)**.

-   **Memory (QuestDB):** A high-performance time-series database for market ticks and audit logs. Accessible on port `9000` (Console) and `8812` (Postgres wire).
-   **Nervous System (Redis):** The asynchronous message bus facilitating communication between the brain and execution layers on port `6379`.
-   **Eyes (Ingestor):** Streams real-time market data (via Polygon.io or Alpaca) directly into QuestDB.
-   **Brain (Analyst Swarm):** A LangGraph-orchestrated AI that analyzes market sentiment, technicals, and fundamentals to generate trades.
-   **Hands (EMS):** The Execution Management System, which handles brokerage adapters (Robinhood, Coinbase, Kalshi) to execute orders via the Redis bus.
-   **Face (Frontend UI):** A real-time dashboard (Deephaven or Streamlit) for visualizing operations and AI reasoning on port `8501` / `10000`.

---

## 🛠️ Components & Ports

| Service | Port | Description |
| :--- | :--- | :--- |
| **QuestDB** | 9000 / 8812 | Data Storage & Querying |
| **Redis** | 6379 | Messaging & Pub/Sub |
| **Deephaven UI** | 10000 | Advanced Dashboarding |
| **FastAPI Backend** | 8000 | Core Internal APIs |
| **Frontend Dashboard** | 8501 | Streamlit/React UI |

---

## 🔮 Future Development

Our next phase of development focuses on:
-   **Core Trading Logic Expansion:** Integrating advanced quantitative strategies into the LangGraph orchestrator.
-   **Sentiment Alpha:** Scaling the X (Twitter) and news analysis modules for predictive signals.
-   **Institutional Scaling:** Enhancing the FIX adapter for broader Prediction Market coverage.
-   **Backtesting Engine:** Leveraging QuestDB for historical replay and strategy validation.

---

**Copyright (c) 2026 Cemini23 / Claudio Barone Jr.**
