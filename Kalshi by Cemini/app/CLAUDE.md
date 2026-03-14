# Kalshi by Cemini — App (FastAPI :8000)

FastAPI backend for the Kalshi prediction market trading system.

## Entry Point

`app/main.py` — FastAPI app; mounts API router; starts Harvester + CeminiAutopilot on startup.

## Structure

```
app/
  api/routes.py      — HTTP endpoints
  core/config.py     — settings (env vars)
  core/database.py   — Postgres init
  models/            — Pydantic schemas
modules/
  satoshi_vision/harvester.py  — Kalshi market scanner
  execution/autopilot.py       — order execution loop
```

## Key Notes

- Port 8000 (FastAPI); `/openapi.json` for schemathesis
- Prometheus metrics via `prometheus_fastapi_instrumentator` at `/metrics`
- Kalshi API env: `KALSHI_API_KEY`, `KALSHI_CONFIG_DIR` (D1 in LESSONS.md)
- `KALSHI_AUTOPILOT_LIVE=true` required for live trades (same guard pattern as C5/C7)
- Image baked — rebuild required after code changes (private_key.pem is volume-mounted)

## Docker

Service: `kalshi_autopilot` in root `docker-compose.yml`
Networks: `app_net` + `data_net`
