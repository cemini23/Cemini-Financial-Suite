**Last Audit:** 2026-02-22 | **Version:** 15.0.0 | **Status:** ✅ Stable (Paper Mode)

# 💎 QuantOS™ (v15.0.0) | Cemini Financial Suite

Welcome to **QuantOS**, your professional-grade trading engine and the brain of the Cemini Financial Suite.

## 🚀 Quick Start (For New Users)
1.  **Dependencies**: Open your terminal and install the required libraries:
    ```bash
    pip3 install -r requirements.txt
    ```
2.  **Configuration**: Open the `.env` file and enter your API keys for Robinhood or Alpaca.
3.  **Launch**: Run the master script from your Desktop to start everything at once:
    ```bash
    python3 ~/Desktop/SuiteLauncher.py
    ```

## 🏗 What is QuantOS?
QuantOS is an automated execution engine that manages your stock and crypto portfolio. It is designed to work in tandem with the Kalshi bot to provide a unified financial dashboard.

## 🚀 New in v15.0.0
- **Intel Bus (Shared Intelligence Layer)**: New `core/intel_bus.py` — a Redis-backed cross-system signal bus. QuantOS publishes `intel:vix_level`, `intel:spy_trend`, `intel:portfolio_heat`, and `intel:btc_volume_spike`. Reads `intel:fed_bias` and `intel:social_score` from Kalshi modules to enhance confidence scoring.
- **Portfolio Heat Guard**: `TradingEngine` and `CeminiAutopilot` automatically pause new positions if combined cross-system load exceeds 80% of capacity.
- **Confluence Score Bonuses**: +5% confidence when Fed is dovish, +3% when social sentiment is positive — both sourced from the Intel Bus.
- **Paper Mode Kill Switch**: All execution paths locked to simulation via `config/dynamic_settings.json` (`environment: PAPER`).
- **Redis Authentication**: All Redis connections now pass `REDIS_PASSWORD` for hardened security.
- **QuantOSBridge Replaced**: HTTP inter-service calls removed. Cross-system data flows through the shared Redis Intel Bus.

## 🚀 In v13.0.0
- **24/7 Real-Time Harvester**: Optimized for around-the-clock data collection via Alpaca real-time streams and burst-mode scanners.
- **Multi-Broker Dashboard**: Real-time balance reporting for Robinhood and Kalshi, with paper-trading balances hidden for accuracy.
- **Fail-Safe Synchronization**: Robust historical data syncing using optimized chunking to prevent API rate limits.
- **Unified Master Launcher**: Integrated with `SuiteLauncher.py` for one-click startup of the entire financial ecosystem.

### Key Capabilities:
*   **24/7 Data Harvester**: Automatically records market prices every 10 seconds into `data/historical/` for future AI training.
*   **Multi-Broker Support**: Connects to **Robinhood**, **Alpaca**, **IBKR**, and more.
*   **Smart Dashboard**: A web-based Mission Control showing your real-money balances and live trade logs.
*   **Fail-Safe Logic**: Automatically retries orders if the broker is busy and handles fractional shares with precision.

## 🏛 Suite Integration
QuantOS integrates with Kalshi by Cemini via the **shared Intel Bus** (`core/intel_bus.py`) over the shared Redis instance. Intelligence signals are published and consumed without HTTP calls — this works reliably inside Docker networks. QuantOS acts as the "Banker" for the suite, aggregating net worth across all connected accounts.

## 📄 License
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
