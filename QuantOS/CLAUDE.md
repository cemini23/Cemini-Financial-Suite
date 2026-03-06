# QuantOS

Stock/crypto trading engine. FastAPI on port 8001.

## Key Components

| File | Role |
|------|------|
| `core/brain.py` (QuantBrain) | RSI via numpy, rolling 1000-price window |
| `core/execution.py` | Buy/sell/bracket + paper mode |
| `core/sentiment/nlp_engine.py` | ProsusAI/finbert pipeline |
| `core/brokers/factory.py` | Dispatches to correct broker |
| `core/brokers/router.py` | Health-checks brokers |
| `core/brokers/alpaca.py` | Primary. Paper: paper-api.alpaca.markets |
| `core/brokers/robinhood.py` | Fractional orders + circuit breaker |

## Known Issues

- RSI uses SMA, not standard Wilder's SMMA — known, do NOT fix without approval
- `RiskManager.check_exposure()` is computed but never blocks trades
- `fresh_start_pending = True` on every restart → forces paper liquidation (dangerous in live)
- BigQuery table mismatch: harvester writes `market_data`, signals read `market_ticks`
- `history_cache` in RAM, lost on restart

## Data Sources

- Primary: Alpaca Algo Trader Plus (core data spine)
- Equity ticks: Polygon (skips when market closed — RSI stale outside 9:30-16:00 ET)
- Crypto: BTC/ETH via Polygon (can show RSI=100 if price unchanged)

## Rebuild Required After

Dockerfile.brain bakes agents/ — any agent change requires `docker compose build brain`.
