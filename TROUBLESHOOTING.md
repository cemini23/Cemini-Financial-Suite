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

### 3. Virtual Memory Mapping (QuestDB)
**Issue:** High-performance databases like QuestDB may crash with `errno=12` if the Docker VM's memory map limit is too low.
**Solution:** Increase the `vm.max_map_count` in the Docker VM:
```bash
docker run --privileged --rm alpine sysctl -w vm.max_map_count=1048576
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

### 2. QuestDB Rust Compiler Error
**Issue:** The official `questdb` Python library may fail to install or compile on ARM64 due to missing Rust dependencies or binary incompatibilities.
**Solution:** Use the standard PostgreSQL wire protocol. Connect via `psycopg2-binary` on port `8812` instead of the proprietary QuestDB client.
**Host:** `questdb` (within Docker) or `localhost` (outside)
**Port:** `8812`

---
**Maintained by Gemini CLI for Cemini Financial Suite.**
