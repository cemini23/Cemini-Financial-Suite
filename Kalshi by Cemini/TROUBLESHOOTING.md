# 🛠️ Kalshi Troubleshooting Guide

## 🌐 Dashboard Won't Load (Port 8000)
*   **Fix**: Another application is using Port 8000. Run the master launcher again to auto-clear the port:
    `python3 ~/Desktop/SuiteLauncher.py`

## 🔑 Authentication Fails
*   **Kalshi**: Ensure your `KALSHI_API_KEY` in `.env` is the "Key ID" from the website, and that your `private_key.pem` is correctly formatted.
*   **X (Twitter)**: If your social feed is empty, you may have run out of API credits. Check the budget bar on the dashboard.

## 🚜 Harvester or Autopilot is slow
*   **Reason**: The bot uses "Burst Mode" to avoid being banned by APIs. 
*   **Fix**: Be patient! It scans in cycles. You can check the "System Intelligence Feed" on the dashboard to see exactly what it's doing.

## 📈 Ticker Not Found
*   **Reason**: Kalshi sometimes renames their series (e.g., from `HIGHMIA` to `KXHIGHMIA`). 
*   **Fix**: I have implemented **Dynamic Discovery** to find the right ticker automatically, but if a market is closed, the bot will skip it.

## 🩺 System Scan
Run the Auditor anytime to verify your setup:
`python3 ~/Desktop/audit_nexus.py`
