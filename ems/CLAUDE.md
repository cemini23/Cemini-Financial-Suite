# EMS — Execution Management System

Standalone EMS package used by the root-level Brain container.
Handles order routing to Kalshi REST v2, Coinbase, Robinhood, and HardRock.

## Files

- `main.py` — Redis subscriber; routes `trade_signals` to adapters; writes `trade_history`
- `kalshi_rest.py` — KalshiRESTv2 raw client (not the BaseExecutionAdapter wrapper)
- `kalshi_ping.py` — one-shot health check for Kalshi REST v2

## Key Notes

- `PAPER_MODE=true` → log-only, no live orders
- Kalshi REST v2 private key mounted at `/app/private_key.pem`
- `KalshiRESTv2` (this dir) vs `KalshiRESTAdapter` (core/ems/adapters/) — different classes; see D14 in LESSONS.md
- `cemini_contracts` and `logit_pricing` are baked into the image (Dockerfile.ems) — rebuild required for changes
- `@beartype` is used on all critical EMS + intel_bus functions

## Networks

`app_net` + `data_net`

## Adapters

| Adapter | Exchange |
|---------|---------|
| CoinbaseAdapter | Coinbase crypto |
| RobinhoodAdapter | Equities (paper) |
| HardRockBetAdapter | HardRock sports betting |
| KalshiRESTv2 | Kalshi prediction markets |
