# Schema Migrations (dbmate)

Step 38 introduced [dbmate](https://github.com/amacneil/dbmate) as the schema migration
framework. All database schema changes go through versioned, idempotent SQL migration
files — no ad-hoc `ALTER TABLE` commands, no schema drift between environments.

---

## Why dbmate

dbmate was chosen over Alembic for three reasons:
1. **Pure SQL** — migrations are plain `.sql` files, readable without Python context
2. **Single binary** — `dbmate` at `/usr/local/bin/dbmate`, no Python environment needed
3. **Idempotent up/down** — transactional migrations with rollback support

---

## Migration Inventory

| File | Date | Contents |
|---|---|---|
| `20260307000000_baseline.sql` | Mar 7 | 9 core tables, `v_correlation_metrics` view, 3 indexes |
| `20260307000001_add_pgvector_extension.sql` | Mar 7 | `CREATE EXTENSION vector` for semantic search |
| `20260307000003_discovery_audit_log.sql` | Mar 7 | `discovery_audit_log` hypertable (TimescaleDB) |
| `20260308000000_intel_embeddings.sql` | Mar 8 | `intel_embeddings` table with HNSW index |
| `20260313000000_fix_cagg_offsets.sql` | Mar 13 | `raw_market_ticks` hypertable + `market_ticks_1min` CAGG |
| `20260313000001_create_fred_observations.sql` | Mar 13 | `fred_observations` table |
| `20260314000000_add_intel_dead_letters.sql` | Mar 14 | `intel_dead_letters` table (pipeline resilience) |
| `20260314130000_add_edgar_tables.sql` | Mar 14 | `edgar_fundamentals`, `edgar_filings_log` |
| `20260314200000_create_audit_hash_chain.sql` | Mar 14 | `audit_hash_chain`, `audit_batch_commitments`, `audit_intent_log` + PL/pgSQL trigger |

---

## Running Migrations

```bash
# Apply all pending migrations
dbmate up

# Check current migration status
dbmate status

# Create a new migration
dbmate new add_my_table

# Roll back last migration
dbmate down
```

dbmate is also deployed as a Docker service that runs `dbmate up` on every deploy:

```yaml
dbmate:
  image: ghcr.io/amacneil/dbmate:2
  command: up
  environment:
    DATABASE_URL: "postgres://admin:${POSTGRES_PASSWORD}@postgres:5432/qdb?sslmode=disable"
  restart: "no"  # exits after running
```

The `restart: "no"` policy ensures the migration service exits cleanly after applying
migrations — it doesn't try to restart as a long-running service.

---

## Database Schema Overview

### Core Tables

| Table | Purpose | Key Columns |
|---|---|---|
| `raw_market_ticks` | OHLCV tick data | `symbol`, `timestamp` (TimescaleDB hypertable) |
| `market_ticks_1min` | 1-minute CAGG | Continuous aggregate of `raw_market_ticks` |
| `trade_history` | Executed trades | `symbol`, `action`, `quantity`, `price` |
| `portfolio_snapshots` | Portfolio state | `timestamp`, `total_value`, `positions_json` |
| `signals` | Generated signals | `detector`, `symbol`, `confidence`, `entry_price` |

### Intelligence Tables

| Table | Purpose |
|---|---|
| `intel_embeddings` | pgvector semantic search (384-dim, HNSW index) |
| `fred_observations` | FRED macro time series (8 series) |
| `edgar_fundamentals` | SEC XBRL fundamentals per CIK + period |
| `edgar_filings_log` | All EDGAR filings with accession numbers |

### Audit Tables

| Table | Purpose |
|---|---|
| `audit_hash_chain` | SHA-256 chained audit entries with UUIDv7 IDs |
| `audit_batch_commitments` | Daily Merkle root commitments |
| `audit_intent_log` | Pre-evaluation signal intents |
| `intel_dead_letters` | Failed pipeline events for replay |
| `discovery_audit_log` | Opportunity screener scan audit |

---

## TimescaleDB Extensions

Three TimescaleDB-specific features are used:

**1. Hypertable** (`raw_market_ticks`):
```sql
SELECT create_hypertable('raw_market_ticks', 'timestamp', if_not_exists => TRUE);
```
Partitions tick data by time for fast range queries.

**2. Continuous Aggregate** (`market_ticks_1min`):
```sql
CREATE MATERIALIZED VIEW market_ticks_1min
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', timestamp) AS bucket,
       symbol, first(open, timestamp), max(high), min(low), last(close, timestamp), sum(volume)
FROM raw_market_ticks
GROUP BY bucket, symbol;
```
Auto-refreshed as new ticks arrive (`end_offset='1 minute'`).

**3. Policies**:
- Compression after 7 days
- Retention after 90 days (automatic old-data cleanup)

---

## Known Pitfall: SERIAL PK on Hypertables

PostgreSQL `SERIAL` primary keys create a `UNIQUE` constraint on a single column.
TimescaleDB requires that all unique constraints on a hypertable include the time
partitioning column. Migration `20260313000000` drops the SERIAL PK before creating
the hypertable:

```sql
ALTER TABLE raw_market_ticks DROP CONSTRAINT IF EXISTS raw_market_ticks_pkey;
SELECT create_hypertable('raw_market_ticks', 'timestamp', if_not_exists => TRUE);
```

---

## pg_dump Wrapper

dbmate's `dump` command calls `pg_dump` — which is inside the postgres container,
not on the host. A wrapper at `/usr/local/bin/pg_dump` delegates to Docker:

```bash
#!/bin/bash
docker exec postgres pg_dump "$@"
```

This allows `dbmate dump` to work transparently from the host.
