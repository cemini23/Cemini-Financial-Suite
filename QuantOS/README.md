**Last Audit:** 2026-02-19 10:08 | **Version:** 13.0.31 | **Status:** ✅ Stable

# 💎 QuantOS™ (v13.0.0) | Cemini Financial Suite

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

## 🚀 New in v13.0.0
- **24/7 Real-Time Harvester**: Optimized for around-the-clock data collection via Alpaca Real-time streams and burst-mode scanners.
- **Multi-Broker Dashboard**: Real-time balance reporting for Robinhood and Kalshi , with Paper-trading balances hidden for accuracy.
- **Fail-Safe Synchronization**: Robust historical data syncing using optimized chunking to prevent API rate limits.
- **Unified Master Launcher**: Integrated with `SuiteLauncher.py` for one-click startup of the entire financial ecosystem.

### Key Capabilities:
*   **24/7 Data Harvester**: Automatically records market prices every 10 seconds into `data/historical/` for future AI training.
*   **Multi-Broker Support**: Connects to **Robinhood**, **Alpaca**, **IBKR**, and more.
*   **Smart Dashboard**: A web-based Mission Control showing your real-money balances and live trade logs.
*   **Fail-Safe Logic**: Automatically retries orders if the broker is busy and handles fractional shares with precision.

## 🏛 Suite Integration
QuantOS runs on **Port 8001**. It acts as the "Banker" for the suite, aggregating your total net worth from all connected accounts.

## 📄 License
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
