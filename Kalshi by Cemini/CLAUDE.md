# Kalshi by Cemini

Prediction market engine. FastAPI on port 8000.

## Key Components

| File | Role |
|------|------|
| `modules/execution/autopilot.py` (CeminiAutopilot) | Orchestrates all modules |
| `modules/satoshi_vision/analyzer.py` | BTC multi-timeframe TA |
| `modules/powell_protocol/analyzer.py` | Fed rate analysis (USES MOCK DATA) |
| `modules/weather_alpha/analyzer.py` | Weather contracts — LIVE Kalshi API |
| `modules/social_alpha/analyzer.py` | X trader sentiment — LIVE X API |
| `modules/musk_monitor/predictor.py` | Musk tweet velocity |
| `rover_runner.py` | Paginates all open Kalshi markets via WebSocket |

## Safety Guards (Step 33)

| Env Var | Default | Effect |
|---------|---------|--------|
| `SOCIAL_ALPHA_LIVE` | `false` | Gated — returns score=0/NEUTRAL |
| `WEATHER_ALPHA_LIVE` | `false` | Gated — returns no opportunities |

Set to `true` in `.env` only when live X API and Kalshi markets are confirmed active.

## Key Rules

- RSA-PSS signing for all Kalshi API requests (`cryptography` lib)
- `.env` at `Kalshi by Cemini/.env` (separate from root `.env`)
- `kalshi_fix.py get_buying_power()` always returns hardcoded $1000 — known issue
- websockets v16: use `additional_headers` not `extra_headers`

## Scoring Flow

```
SatoshiAnalyzer → btc_score
PowellAnalyzer  → yield_curve
SocialAnalyzer  → social_score  [GATED by SOCIAL_ALPHA_LIVE]
WeatherAnalyzer → best_opp      [GATED by WEATHER_ALPHA_LIVE]
MuskPredictor   → musk_status
         ↓
CeminiAutopilot.scan_and_execute() → Kelly allocation → order
```
