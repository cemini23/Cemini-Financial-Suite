# Kalshi by Cemini — Prediction Market Engine

<!-- AUTO:LAST_UPDATED -->
*Auto-generated: 2026-03-01 15:50 UTC*
<!-- /AUTO:LAST_UPDATED -->

## Overview

Prediction market trading engine for Kalshi. Integrates multi-domain analysis (BTC,
Fed rates, weather, geopolitical) with Kelly Criterion position sizing and RSA-signed
API execution.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| Autopilot | `modules/execution/autopilot.py` | Main 30s scan-and-execute loop |
| SatoshiAnalyzer | `modules/satoshi_vision/analyzer.py` | Multi-timeframe BTC TA (SCALP/SWING/MACRO) |
| PowellAnalyzer | `modules/powell_protocol/analyzer.py` | Treasury yields + rate decision analysis |
| WeatherAnalyzer | `modules/weather_alpha/analyzer.py` | NWS/OpenWeather forecast consensus |
| SocialAnalyzer | `modules/social_alpha/analyzer.py` | X/Twitter sentiment (⚠️ simulated data) |
| MuskPredictor | `modules/musk_monitor/predictor.py` | Tweet velocity + empire/launch data model |
| GeoPulseMonitor | `modules/geo_pulse/monitor.py` | Geopolitical signals — live GDELT fallback via Redis |
| MarketRover | `modules/market_rover/rover.py` | Cross-references QuantOS sentiment with Kalshi markets |
| CapitalAllocator | `modules/execution/allocator.py` | Kelly Criterion position sizing |

## Data Gaps

- `social_alpha/analyzer.py` — Uses hardcoded simulated tweets (not live X API)
- `powell_protocol/analyzer.py` — Mock Kalshi rate bracket prices (not live)
- `weather_alpha/analyzer.py` — Simulated order book prices (not live)
- `geo_pulse/monitor.py` — Falls back to live GDELT data from Redis (`intel:conflict_events`);
  if Redis unavailable, uses X API; if both unavailable, returns NO_SIGNAL

## Running

```bash
docker compose up -d kalshi_autopilot rover_scanner
docker logs kalshi_autopilot --since '30 minutes ago'
```
