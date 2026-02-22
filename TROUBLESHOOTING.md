# 🛠️ Universal Troubleshooting Guide

This document captures critical fixes and architectural patterns for the Cemini Financial Suite. While the suite is hardware-agnostic, some environments may require specific configurations.

## 🟢 General Docker & Python Fixes

### 1. Silent Docker Logs
**Issue:** Python buffers its output by default, causing `docker logs` to appear empty or significantly delayed.
**Solution:** Every Dockerfile in the suite must include `ENV PYTHONUNBUFFERED=1` to ensure logs are streamed in real-time for debugging.

### 2. Kalshi API DNS & Connectivity
**Issue:** Legacy endpoints may become inactive, resulting in `[Errno -2] Name or service not known`.
**Solution:**
- Ensure you are using the active endpoint: `demo-api.kalshi.co`.
- If Docker loses internet access entirely (common on some desktop bridge networks), restart Docker Desktop to flush the internal DNS resolver.

### 3. Virtual Memory Mapping (TimescaleDB)
**Issue:** TimescaleDB or other high-performance databases may crash with `errno=12` if the Docker VM's memory map limit is too low.
**Solution:** Increase the `vm.max_map_count` in the Docker VM:
```bash
docker run --privileged --rm alpine sysctl -w vm.max_map_count=1048576
```

### 4. Redis Authentication Errors (`WRONGPASS` / `NOAUTH`)
**Issue:** Services fail to connect to Redis with `WRONGPASS` or `NOAUTH` errors after Redis password enforcement was added.
**Solution:** Ensure `REDIS_PASSWORD` in your `.env` matches the password configured in `docker-compose.yml`. The default is `cemini_redis_2026`.
```bash
# In .env
REDIS_PASSWORD=cemini_redis_2026
```
If you changed the password, update both files and restart Redis:
```bash
docker compose restart redis
```

### 5. Intel Bus Returns `None` for All Keys
**Issue:** `IntelReader.read()` or `IntelReader.read_async()` returns `None` for `intel:*` keys even when services are running.
**Cause:** The publishing service hasn't completed its first cycle yet (e.g., `analyzer.py` publishes `intel:vix_level` only on the hourly review). Bus keys also expire after 300 seconds of inactivity.
**Solution:** Wait for at least one full cycle of the publishing service to complete, or manually trigger a review. Check Redis directly:
```bash
docker exec -it redis redis-cli -a cemini_redis_2026 keys "intel:*"
```

---

## 🟡 Hardware-Specific Edge Cases: Apple Silicon (ARM64)

### 1. M4 Venv Corruption
**Issue:** Moving virtual environments across different directories or restore points on M-series Macs can break `pip` and shared libraries.
**Solution:** Do not attempt to repair a corrupted `venv`. Always wipe the directory and recreate it natively on the hardware:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. TimescaleDB Connection on ARM64
**Issue:** On Apple Silicon, the `psycopg2` library may fail to compile from source.
**Solution:** Always install `psycopg2-binary` (pre-compiled wheel) rather than `psycopg2`. The suite's `requirements.txt` already specifies this.
**Host:** `postgres` (within Docker) or `localhost` (outside Docker)
**Port:** `5432`

---
**Maintained by Cemini Financial Suite. Copyright (c) 2026 Cemini23 / Claudio Barone Jr.**
