# Cemini Scrapers — CLAUDE.md

Service notes for all scrapers in this directory.
Read this before modifying any scraper service.

---

## macro_harvester.py

Purpose: Pulls 10Y Treasury yield (yfinance) and Fear & Greed Index (alternative.me).
Publishes: `macro:10y_yield`, `macro:fear_greed` (raw Redis SET, no IntelPublisher envelope).
Poll: 300s.

---

## gdelt_harvester.py

Purpose: Scans GDELT global event database for geopolitical signals affecting markets.
Publishes: `intel:gdelt_*` channels via IntelPublisher.
Archive: `/mnt/archive/gdelt/`
Poll: `GDELT_SCAN_INTERVAL` env var (default 900s).

---

## fred_monitor.py (Step 39)

Purpose: Polls Federal Reserve Economic Data (FRED) API for 12 key macro series and
publishes intelligence to Redis `intel:fred_*` channels.

**Series polled (12 total):**

| Series ID     | Channel                  | Field                  | Freq    |
|---------------|--------------------------|------------------------|---------|
| T10Y2Y        | intel:fred_yield_curve   | spread_10y2y           | daily   |
| T10Y3M        | intel:fred_yield_curve   | spread_10y3m           | daily   |
| DFF           | intel:fred_fed_policy    | fed_funds_rate         | daily   |
| WALCL         | intel:fred_fed_policy    | fed_balance_sheet_mm   | weekly  |
| BAMLH0A0HYM2  | intel:fred_credit_spread | hy_oas_spread          | daily   |
| ICSA          | intel:fred_labor         | initial_claims         | weekly  |
| UNRATE        | intel:fred_labor         | unemployment_rate      | monthly |
| PAYEMS        | intel:fred_labor         | nonfarm_payrolls_k     | monthly |
| PCEPI         | intel:fred_inflation     | pce_index              | monthly |
| CPILFESL      | intel:fred_inflation     | core_cpi_index         | monthly |
| UMCSENT       | intel:fred_sentiment     | michigan_sentiment     | monthly |
| VIXCLS        | intel:fred_sentiment     | vix_close              | daily   |

**Configuration:**
- Poll interval: 900s (15 min)
- Redis TTL: 1800s (2× poll interval — LESSONS.md TTL mismatch pattern)
- FRED rate limit: 0.6s sleep between API calls (120 req/min allowed)
- Backfill: 90 days on startup (idempotent via ON CONFLICT DO NOTHING)

**Redis channels:**
All payloads use IntelPublisher envelope format:
```json
{
  "value": {"spread_10y2y": 0.42, "observation_date": "2026-03-12", "source": "fred"},
  "source_system": "fred_monitor",
  "timestamp": 1741824000.0,
  "confidence": 1.0
}
```

**PostgreSQL table:** `fred_observations`
Migration: `db/migrations/20260313000001_create_fred_observations.sql`

**JSONL archive:** `/mnt/archive/fred/fred_YYYYMMDD.jsonl`

**Known gotchas:**
- FRED returns `"."` (a literal dot string) for missing/unreported values — NOT null. `_parse_fred_value(".")` returns `None`.
- Some series (UNRATE, PAYEMS, PCEPI, CPILFESL, UMCSENT) update monthly. Do not alert on "stale" data — it is expected.
- WALCL and ICSA are weekly. VIX/yield curve series are daily.
- FRED_API_KEY must be in `.env`. Service logs a warning and sleeps 60s if missing — does NOT crash.
- TTL (1800s) must remain >= 2× poll interval (900s). See LESSONS.md.
