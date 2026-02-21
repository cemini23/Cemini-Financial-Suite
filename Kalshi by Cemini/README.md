**Last Audit:** 2026-02-19 10:08 | **Version:** 2.0.31 | **Status:** ✅ Stable

# 🔮 Kalshi by Cemini (v2.0.0) | Cemini Financial Suite

Welcome to **Kalshi by Cemini**, your automated command center for event-contract arbitrage and high-speed prediction markets.

## 🚀 One-Click Setup
1.  **Run the Installer**:
    ```bash
    ./RUN_KALSHI.sh
    ```
    This will automatically create your environment and install all tools.
2.  **Add Your Keys**: Open the `.env` file and paste your Kalshi Email, Password, and API Key.
3.  **Private Key**: Ensure your `private_key.pem` file is located in this folder.

## 🧠 The Intelligence Modules
This bot uses 4 distinct "Brains" to find trades:
*   **Weather Alpha**: Scans the entire US for temperature arbitrage opportunities.
*   **Musk Monitor**: Tracks Elon Musk's behavior and tweets to predict event outcomes.
*   **Social Alpha**: Analyzes the top crypto influencers on X (Twitter) using AI.
*   **Satoshi Vision**: Uses institutional math to find high-probability BTC setups.

## 🛡️ Built-in Safety
*   **Budget Guard**: Automatically stops scanning if you hit 90% of your X API budget.
*   **Portfolio Guard**: Never buys the same trade twice in one day.
*   **Exit Engine**: Automatically sells to lock in profits at 90c or cut losses at 10c.

## 🏛 Suite Integration
Kalshi runs on **Port 8000** and connects directly to QuantOS to share intelligence.

## 🚦 Usage
To start the full suite, use the master button on your Desktop:
`python3 ~/Desktop/SuiteLauncher.py`
