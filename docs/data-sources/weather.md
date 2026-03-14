# Weather Data — Visual Crossing

The Weather Alpha module uses weather forecast data to generate arbitrage signals for weather-sensitive Kalshi prediction market contracts. It is gated behind the `WEATHER_ALPHA_LIVE` safety guard (C7).

---

## Role

- Fetch multi-day weather forecasts from Visual Crossing (primary) and NWS/OpenMeteo (backup)
- Compute agricultural metrics: Growing Degree Days (GDD), Heating Degree Days (HDD), Cooling Degree Days (CDD)
- Identify divergence between forecast data and Kalshi market implied probabilities
- Publish weather arbitrage signals to the Intel Bus

---

## Five Data Sources

The `weather_alpha` module polls five sources in priority order:

1. **Visual Crossing** (primary) — paid API, high data quality, includes high/low temps
2. **NWS (National Weather Service)** — free, US-only, government authority
3. **Open-Meteo** — free, global coverage
4. **OpenWeatherMap** — free tier, backup
5. **WeatherAPI.com** — free tier, backup

If any source fails, the next source in the list is tried. Circuit breaker prevents cascade failures.

---

## Safety Guard C7

```bash
# Required to enable live weather signals:
WEATHER_ALPHA_LIVE=true
```

When `WEATHER_ALPHA_LIVE` is not `true`, the weather analyzer returns neutral signals. This prevents unvalidated weather-market correlations from influencing live Kalshi trading.

**Key implementation note:** The WeatherAnalyzer includes a zero-bid guard:

```python
# Zero-bid Kalshi contracts cause ZeroDivisionError in profit calculation
if 0 < bid_price < 0.30:
    # Skip extreme mispricing — not a genuine arbitrage opportunity
    continue
```

---

## Agricultural Metrics

For commodity and agricultural ETF/futures Kalshi contracts, the harvester computes:

| Metric | Formula | Use Case |
|---|---|---|
| GDD (base 50°F) | max(0, (high+low)/2 − 50) | Corn/soybean crop development |
| GDD (base 41°F) | max(0, (high+low)/2 − 41) | Winter wheat emergence |
| HDD | max(0, 65 − (high+low)/2) | Heating demand proxy |
| CDD | max(0, (high+low)/2 − 65) | Cooling demand proxy |

---

## Intel Bus Output

```
intel:weather_signal → {
    "temperature_forecast": [...],
    "precipitation_forecast": [...],
    "gdd_base50": 12.5,
    "hdd": 8.0,
    "cdd": 0.0,
    "arbitrage_signal": "buy_no_rain",
    "confidence": 0.72,
    "source": "visual_crossing",
    "fetched_at": "2026-03-14T12:00:00Z"
}
TTL: 3600s (1 hour)
```
