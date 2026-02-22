**Last Audit:** 2026-02-22 | **Version:** 2.1.0 | **Status:** ✅ Stable (Paper Mode)

# 🔮 Kalshi by Cemini (v2.1.0) | Cemini Financial Suite

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
*   **Weather Alpha**: Scans the entire US for temperature arbitrage opportunities. Publishes `intel:weather_edge` to the Intel Bus.
*   **Musk Monitor (Powell Protocol)**: Tracks Fed communications and macro catalysts to predict rate decisions. Publishes `intel:fed_bias` to the Intel Bus.
*   **Social Alpha**: Analyzes the top crypto influencers on X (Twitter) using AI. Publishes `intel:social_score` to the Intel Bus.
*   **Satoshi Vision**: Uses institutional math to find high-probability BTC setups. Publishes `intel:btc_sentiment` to the Intel Bus.

## 🛡️ Built-in Safety
*   **Budget Guard**: Automatically stops scanning if you hit 90% of your X API budget.
*   **Portfolio Guard**: Never buys the same trade twice in one day.
*   **Exit Engine**: Automatically sells to lock in profits at 90c or cut losses at 10c.
*   **Portfolio Heat Guard**: Reads `intel:portfolio_heat` from the shared Intel Bus. If combined active positions across QuantOS and Kalshi exceed 80% of capacity, new trades are automatically skipped.
*   **Paper Mode Kill Switch**: `trading_enabled: false` and `paper_mode: true` in `settings.json`. No live orders are placed until these are explicitly re-enabled.

## 🏛 Suite Integration
Kalshi by Cemini integrates with QuantOS via the **shared Intel Bus** — a Redis-backed signal layer (`core/intel_bus.py`). Both systems publish and read from the same `intel:*` key namespace over the shared Redis instance. There are no HTTP calls between containers; all cross-system intelligence is exchanged through Redis, making the integration reliable in Docker networks where `localhost` inter-service calls fail.

## 🚦 Usage
To start the full suite, use the master button on your Desktop:
`python3 ~/Desktop/SuiteLauncher.py`
