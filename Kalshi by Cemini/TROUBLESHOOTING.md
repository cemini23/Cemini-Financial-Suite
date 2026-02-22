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

## 🔌 Intel Bus / Redis Issues

### Intelligence modules show `None` for cross-system signals
*   **Cause**: The Intel Bus key has expired (TTL: 300 seconds) or the publishing service hasn't completed a cycle yet.
*   **Fix**: Confirm Redis is running and the signal key exists:
    ```bash
    docker exec -it redis redis-cli -a cemini_redis_2026 keys "intel:*"
    ```

### `WRONGPASS` or `NOAUTH` connecting to Redis
*   **Cause**: The `REDIS_PASSWORD` env var in `.env` doesn't match the password in `docker-compose.yml`.
*   **Fix**: Ensure `.env` contains `REDIS_PASSWORD=cemini_redis_2026` (or your custom password). Then restart:
    ```bash
    docker compose restart redis
    ```

### Autopilot skipping all trades with "Portfolio heat" message
*   **Cause**: `intel:portfolio_heat` on the bus is above 0.8 — combined QuantOS + Kalshi positions are near capacity.
*   **Fix**: This is intentional risk management. Wait for existing positions to close, or check `quantos:active_positions` and `kalshi:executed_trades` keys in Redis for the current position counts.

## 🩺 System Scan
Run the Auditor anytime to verify your setup:
`python3 ~/Desktop/audit_nexus.py`
