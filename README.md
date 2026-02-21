# Cemini Financial Suite

![Multi-Architecture Ready](https://img.shields.io/badge/Multi--Architecture-amd64%20%7C%20arm64-blue)
![Cross-Platform](https://img.shields.io/badge/Cross--Platform-Windows%20%7C%20Linux%20%7C%20macOS-green)

The **Cemini Financial Suite** is a **Universal, Cross-Platform Trading Architecture** designed for high-frequency financial operations. Built on a modular, Dockerized foundation, it integrates real-time market data, AI-driven decision-making, and institutional execution into a unified, hardware-agnostic environment.

## 🏗️ Architecture: "The Body"

The suite is designed as a modular organism, where each service plays a critical role. Because it leverages Docker, Redis, and standard PostgreSQL wire protocols, it runs seamlessly on **Windows (WSL2), Linux Servers, Intel Macs, and Apple Silicon (M-series)**.

-   **Memory (QuestDB):** A high-performance time-series database for market ticks and audit logs. Accessible on port `9000` (Console) and `8812` (Postgres wire).
-   **Nervous System (Redis):** The asynchronous message bus facilitating communication between the brain and execution layers on port `6379`.
-   **Eyes (Ingestor):** Streams real-time market data (via Polygon.io or Alpaca) directly into QuestDB.
-   **Brain (Analyst Swarm):** A LangGraph-orchestrated AI that analyzes market sentiment, technicals, and fundamentals to generate trades.
-   **Hands (EMS):** The Execution Management System, which handles brokerage adapters (Robinhood, Coinbase, Kalshi) to execute orders via the Redis bus.
-   **Face (Frontend UI):** A real-time dashboard (Deephaven or Streamlit) for visualizing operations and AI reasoning on port `8501` / `10000`.

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Docker Desktop** (or Docker Engine with Compose)
- **Python 3.11+**
- **Git**

### 2. Environment Configuration
Create a `.env` file in the root directory (based on the provided structure) and populate your API keys for Polygon, Alpaca, and your brokerage credentials.

### 3. Native Virtual Environment
To ensure cross-platform compatibility, always create the environment natively for your OS:
```bash
# From the project root
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 4. Master Launch Command
Start the entire infrastructure in one command:
```bash
docker-compose up -d --build
```

---

## 🛠️ Components & Ports
| Service | Port | Description |
| :--- | :--- | :--- |
| **QuestDB** | 9000 / 8812 | Data Storage & Querying |
| **Redis** | 6379 | Messaging & Pub/Sub |
| **Deephaven UI** | 10000 | Advanced Dashboarding |
| **FastAPI Backend** | 8000 | Core Internal APIs |
| **Frontend Dashboard**| 8501 | Streamlit/React UI |

---

## 🔮 Future Development
Our next phase of development focuses on:
-   **Core Trading Logic Expansion:** Integrating advanced quantitative strategies into the LangGraph orchestrator.
-   **Sentiment Alpha:** Scaling the X (Twitter) and news analysis modules for predictive signals.
-   **Institutional Scaling:** Enhancing the FIX adapter for broader Prediction Market coverage.
-   **Backtesting Engine:** Leveraging QuestDB for historical replay and strategy validation.

---
**Copyright (c) 2026 Cemini23 / Claudio Barone Jr.**
