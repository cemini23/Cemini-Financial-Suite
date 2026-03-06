# Cemini Financial Suite

Private-use algorithmic trading platform. 18 Docker services on single Hetzner VPS.
Three cooperating engines sharing intelligence via Redis pub/sub.

## Architecture

Root orchestrator (brain + analyzer + EMS) on app_net
QuantOS (FastAPI :8001) — equities/crypto signals
Kalshi by Cemini (FastAPI :8000) — prediction markets
Trading Playbook — observation-only regime/signal/risk layer

## Redis Intelligence Bus

| Channel | Direction | Purpose |
|---------|-----------|---------|
| `trade_signals` | brain → EMS | execution commands |
| `emergency_stop` | broadcast | kill switch |
| `strategy_mode` | brain → all | conservative/aggressive/sniper |
| `intel:*` | all systems | cross-system intelligence |

## Key Rules

- Redis requires auth: `REDIS_PASSWORD` env var
- DB_HOST=postgres, REDIS_HOST=redis (Docker DNS)
- flake8: max-line-length=120, E501 ignored, E999/F821 enforced
- All pre-gate data quarantined at `/opt/cemini/archives/data_quarantine/` — do NOT use
- Do NOT disrupt running harvesters or playbook_runner
- C4: Postgres password reads from `POSTGRES_PASSWORD` env var (never hardcode)
- C5: `SOCIAL_ALPHA_LIVE=true` required for live social signals (default: gated/neutral)
- C7: `WEATHER_ALPHA_LIVE=true` required for live weather signals (default: gated/neutral)

## Networks

| Network | Services |
|---------|---------|
| edge_net | nginx, cloudflared |
| app_net | brain, analyzer, ems, quantos, kalshi, playbook, cemini_os |
| data_net | postgres, redis, pgadmin |

## Completed Steps

Steps 1 (CI/CD), 2 (Docker Networks), 6 (Equity Ticks), 14 (GDELT), 15 (Auto-Docs),
16 (Kalshi WS), 20 (Skill Vetting), 24 (Visual Crossing Weather), 32 (CLAUDE.md),
33 (Safety Guards C4+C5+C7).

## Testing

- All tests in `/opt/cemini/tests/` — pure, no network/Redis/Postgres
- Run: `pytest tests/ -v`
- Current target: 192+ tests, all green, flake8 clean

## Token Efficiency
Always use RTK (installed globally) to compress verbose CLI output before sending to context.
RTK reduces directory trees, error logs, git diffs, and JSON payloads by 60-90%.
