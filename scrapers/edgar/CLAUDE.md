# SEC EDGAR Direct Pipeline (Step 40)

Replaces the $49/mo sec-api.io dependency. Polls SEC EDGAR directly (free, no API key).

## Files

- `edgar_harvester.py` — main service (643 lines); 3 APScheduler jobs + FastAPI /health
- `cik_mapping.py` — CIK lookup map for tracked tickers; EDGAR_HEADERS constant

## Jobs

| Job | Schedule | Redis output |
|-----|----------|-------------|
| `filing_monitor_job` | every 10 min | `intel:edgar_filing` |
| `insider_scanner_job` | every 30 min | `intel:edgar_insider` |
| `fundamentals_job` | daily 06:00 UTC (cron) | Postgres only |

## Rate Limiting

EDGAR allows ≤ 10 req/sec. Use `0.15s` sleep between CIK lookups.
User-Agent header is **required** — requests without it return 403.

## Tables

- `edgar_fundamentals` — UNIQUE on `(cik, period_of_report)` — upserts OK
- `edgar_filings_log` — UNIQUE on `accession_number`

Migration: `db/migrations/20260314130000_add_edgar_tables.sql`

## Redis

- Dedup: `edgar:{prefix}:seen:{accession}` keys (7-day TTL)
- Intel: `intel:edgar_filing` and `intel:edgar_insider` (TTL 600s / 1800s)

## Known Gotchas

- IWM (ETF) has no direct SEC CIK — expected WARNING, skip gracefully
- Form 4 XML: use `ET.fromstring()` with `# noqa: S314` (EDGAR XML is SEC-published, not user input)
- `fundamentals_job` uses `trigger="cron"` (not `add_harvester_job` which is interval-only)
- XBRL facts URL: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json`

## Docker

Service: `edgar_pipeline` in `docker-compose.yml`
Image: `Dockerfile.edgar`
Networks: `app_net` + `data_net`
