# 🛠️ QuantOS™ Troubleshooting Guide

If the bot isn't behaving as expected, check these common solutions.

## 🚀 The "Magic Fix"
Most issues are solved by a clean restart. Run:
`python3 ~/Desktop/SuiteLauncher.py`

---

## 📉 Common Issues

### 1. Dashboard says "Offline"
*   **Cause**: The server didn't start or the port is blocked.
*   **Fix**: Check if any other app is using Port 8001. Run `lsof -i :8001` in your terminal to see what's there.

### 2. Robinhood orders are being rejected
*   **Cause**: Usually "Pattern Day Trader" (PDT) protection or insufficient funds.
*   **Fix**: Ensure your Robinhood account has at least $25,000 for unlimited day trading, or reduce the trade frequency in settings.

### 3. "Quantity 0" Error
*   **Cause**: The bot tried to buy a stock that is too expensive for your current budget using whole shares.
*   **Fix**: I have enabled **Fractional Trading** support. Ensure your broker account supports fractional shares (standard on most modern accounts).

### 4. Harvester isn't creating files
*   **Cause**: Permissions issue in the `data/` folder.
*   **Fix**: Ensure the folder `QuantOS/data/historical` exists and is "writable."

### 5. Intel Bus returning `None` for all `intel:*` keys
*   **Cause**: The publishing service hasn't completed its first cycle, or Redis authentication is failing silently.
*   **Fix**: Check Redis connectivity and inspect bus keys:
    ```bash
    docker exec -it redis redis-cli -a cemini_redis_2026 keys "intel:*"
    ```
    If no keys are returned, check that `analyzer.py` (Coach) is running and has completed its first hourly review. For `intel:btc_volume_spike`, check `signal_generator` logs.

### 6. Redis `WRONGPASS` / `NOAUTH` errors
*   **Cause**: `REDIS_PASSWORD` env var missing or mismatched.
*   **Fix**: Confirm `.env` contains `REDIS_PASSWORD=cemini_redis_2026`. Then restart:
    ```bash
    docker compose restart redis
    ```

---

## 🩺 Health Check
Run the **Cemini Auditor** to auto-fix your environment:
`python3 ~/Desktop/audit_nexus.py`

## 🆘 Still Stuck?
Check the live logs in `Desktop/QuantOS/quantos_suite.log` for the specific error message.
