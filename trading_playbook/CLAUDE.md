# Trading Playbook

Observation-only layer. Logs regime/signal/risk snapshots every 5 min.
Does NOT place orders.

## Key Components

| File | Role |
|------|------|
| `macro_regime.py` | GREEN/YELLOW/RED via SPY vs EMA21/SMA50 + JNK/TLT |
| `signal_catalog.py` | 6 detectors: EpisodicPivot, MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212 |
| `risk_engine.py` | Fractional Kelly (25% cap), CVaR (99th), DrawdownMonitor |
| `kill_switch.py` | PnL velocity, order rate, latency, price deviation → CANCEL_ALL |
| `playbook_logger.py` | Postgres (playbook_logs), JSONL (/mnt/archive/playbook/), Redis |
| `runner.py` | 5-min scan loop; sector rotation runs every 6th cycle (30 min) |
| `sector_rotation.py` | RRG-style RS ratio/momentum/quadrant for 11 SPDR sector ETFs vs SPY; publishes `intel:sector_rotation` (TTL=3600) |

## Data Flow

- Reads: `raw_market_ticks`, `macro_logs` from Postgres
- Writes: `playbook_logs` (JSONB payload), `sector_rotation_log` (JSONB) to Postgres
- Publishes: `intel:playbook_snapshot`, `intel:sector_rotation` to Redis

## Regime Gate Thresholds

| Regime | BUY threshold | SELL/SHORT |
|--------|--------------|-----------|
| GREEN | 0.55 | 0.55 |
| YELLOW | 0.71 | 0.50 |
| RED | 0.74 | 0.45 |

Catalyst bonus: +0.10 for EpisodicPivot/InsideBar212 in YELLOW/RED only.

## Known Issues

- Regime gate uses dynamic confidence thresholds, not binary blocking
- RSI uses SMA not Wilder's SMMA — do NOT "fix" without explicit approval

## Token Efficiency
Always use RTK (installed globally) to compress verbose CLI output before sending to context.
RTK reduces directory trees, error logs, git diffs, and JSON payloads by 60-90%.
