# Kalshi by Cemini — EMS

Legacy Redis-based execution module for Kalshi signal routing.

## Entry Point

`ems/main.py` — subscribes to Redis `trade_signals` channel; calls `handle_signal()`.

## Key Notes

- Uses raw `redis` (not redis.asyncio) with `dotenv` for env loading
- `handle_signal(message)` processes incoming signal JSON
- Superseded in production by the root-level EMS (`/opt/cemini/ems/`) which uses full adapter stack
- Keep in place — referenced by Kalshi by Cemini docker-compose services

## Networks

`app_net` + `data_net`
