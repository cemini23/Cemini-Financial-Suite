# Trading Playbook — Observation & Risk Layer

<!-- AUTO:LAST_UPDATED -->
*Auto-generated: 2026-03-14 20:07 UTC*
<!-- /AUTO:LAST_UPDATED -->

## Overview

Observation-only layer running every 5 minutes. Classifies macro regime, detects
tactical setups, computes risk metrics, and logs everything to Postgres + JSONL for
future RL model training. **Does NOT place orders.**

## Components

| Component | File | Purpose |
|-----------|------|---------|
| Macro Regime | `macro_regime.py` | Traffic-light (GREEN/YELLOW/RED) via SPY vs EMA21/SMA50 + JNK/TLT |
| Signal Catalog | `signal_catalog.py` | 6 detectors: EpisodicPivot, MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212 |
| Risk Engine | `risk_engine.py` | Fractional Kelly (25% cap), CVaR (99th pctile), DrawdownMonitor |
| Kill Switch | `kill_switch.py` | PnL velocity, order rate, latency, price deviation → CANCEL_ALL |
| Logger | `playbook_logger.py` | Postgres (playbook_logs) + JSONL (/mnt/archive/playbook/) + Redis |
| Runner | `runner.py` | 5-min scan loop orchestrating all components |

## Regime Classification

| Regime | Condition | Posture |
|--------|-----------|---------|
| 🟢 GREEN | SPY > rising EMA21 | Aggressive — full position sizing |
| 🟡 YELLOW | SPY < EMA21 but > SMA50 | Defensive — no new longs |
| 🔴 RED | SPY < SMA50 | Survival — cash or short only |

The regime gate in `agents/orchestrator.py` blocks all BUY signals when regime is YELLOW or RED.

## Data Output

- **Postgres:** `playbook_logs` table with JSONB payload (regime, signals, risk metrics)
- **JSONL:** `/mnt/archive/playbook/` — 15+ files per day for RL training corpus
- **Redis:** `intel:playbook_snapshot` — latest regime + signals, consumed by brain + EMS

## Running

```bash
docker compose up -d playbook
docker logs playbook_runner --since '30 minutes ago' | grep regime
```
