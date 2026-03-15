# EDGAR Monitor (Step 17)

Alert logic on top of the Step 40 EDGAR pipeline. Pure subscriber — no
harvesting or scraping.

## Files

| File | Purpose |
|------|---------|
| `alert_rules.py` | Filing significance scoring (0-100, threshold 60) |
| `insider_cluster.py` | Cluster detection: 2+ insiders buying within window |
| `metric_extractor.py` | 8-K item number → event type extraction |
| `models.py` | Pydantic v2: EdgarAlert, FilingSignificance, InsiderCluster |
| `subscriber.py` | Polls intel:edgar_* and emits intel:edgar_alert |

## Data Flow

```
intel:edgar_filing  ──┐
                      ├─► edgar_monitor/subscriber.py ──► intel:edgar_alert
intel:edgar_insider ──┘                                ──► edgar_alerts (Postgres)
                                                       ──► /mnt/archive/edgar_alerts/
                                                       ──► audit_hash_chain
```

## Key Rules

- Reads from `intel:edgar_filing` and `intel:edgar_insider` (SET by Step 40 harvester)
- Alert threshold: significance_score >= 60
- Insider cluster: 2+ distinct insiders buying within 7 days, min $100K total
- `run_monitor_cycle()` is the APScheduler entry point — call every 90s
- ARCHIVE_ROOT: `os.getenv("EDGAR_ALERT_ARCHIVE_DIR", "/mnt/archive/edgar_alerts")`
- All writes are fail-silent (never raises, never blocks)

## Scoring Weights

| Form | Base | Alert at score |
|------|------|----------------|
| S-1  | 80   | Yes (always)   |
| 8-K  | 70   | Yes + boosters |
| SC 13D | 65 | Yes           |
| 4    | 50   | No (unless cluster) |
| 10-K | 40   | No             |

8-K item boosters: 2.02 earnings (+35), 5.02 exec change (+30), 1.01 material agreement (+30)

## Redis

- `intel:edgar_alert` (SET, TTL 3600s) — full EdgarAlert in Intel Bus envelope

## DB Table

- `edgar_alerts` — migration `20260315100000_add_edgar_alerts.sql`

## Docker

No new service. `run_monitor_cycle()` can be scheduled from:
1. The existing `edgar_pipeline` service (APScheduler job)
2. A standalone APScheduler script

## Known Gotchas

- Filing item numbers are parsed from the `description` field via regex `\b(\d\.\d{2})\b`
- Single-trade insider payloads cannot form clusters alone — cluster detection
  requires `_fetch_recent_insider_trades()` to query edgar_filings_log
- `_seen_accessions` is in-process memory — resets on restart (acceptable; TTL on
  intel:edgar_filing is 600s so re-alerts within a session window are possible)
