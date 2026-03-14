# FRED Macro Data

The Federal Reserve Economic Data (FRED) pipeline provides macroeconomic context for regime classification and signal scoring. It is free, authoritative, and covers hundreds of economic series.

---

## Role

- Supply macroeconomic indicators (unemployment, inflation, yield curve, etc.) to the Intel Bus
- Cross-validate equity regime signals with macro conditions
- Feed the Opportunity Screener's conviction scorer

---

## fred_monitor Service

The `fred_monitor` harvester polls the FRED API hourly and publishes a dict of key indicators to `intel:fred_macro` (TTL 3600s).

**Key indicators tracked:**

| Series | Description |
|---|---|
| FEDFUNDS | Federal Funds Rate |
| T10Y2Y | 10-Year minus 2-Year Treasury spread (yield curve) |
| UNRATE | Unemployment Rate |
| CPIAUCSL | Consumer Price Index (CPI) — seasonally adjusted |
| DGS10 | 10-Year Treasury Constant Maturity Rate |
| VIXCLS | CBOE Volatility Index (VIX) |
| BAMLH0A0HYM2 | High-yield credit spread (proxy for risk appetite) |

---

## Intel Bus Integration

```python
# Published every hour by fred_monitor
intel:fred_macro → {
    "fedfunds": 5.25,
    "t10y2y": -0.45,      # negative = inverted yield curve
    "unrate": 4.1,
    "cpiaucsl": 308.4,
    "dgs10": 4.32,
    "vixcls": 18.5,
    "credit_spread": 3.21,
    "fetched_at": "2026-03-14T12:00:00Z"
}
```

---

## JSONL Archive

Every hourly poll result is archived to `/mnt/archive/fred/fred_YYYYMMDD.jsonl` for offline analysis and audit purposes.

---

## Cost

FRED is free with no rate limits for non-commercial use. API key registration at fred.stlouisfed.org is recommended (raises rate limits from 500 to 120,000 requests/day).
