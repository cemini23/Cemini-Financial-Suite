# Changelog — Cemini Financial Suite

All notable changes are recorded here. Dates are UTC.

---

## [Mar 14, 2026]

### Added — Step 43: Cryptographic Audit Trail
- `shared/audit_trail/` package: SHA-256 hash chain (Layer 1), pymerkle daily batches (Layer 2), OpenTimestamps anchoring (Layer 3)
- PL/pgSQL `BEFORE INSERT` trigger auto-computes `prev_hash` + `chain_hash` on every audit row
- New tables: `audit_hash_chain`, `audit_batch_commitments`, `audit_intent_log`
- Pre-evaluation intent logging in `signal_catalog.scan_symbol()` — proves no cherry-picking
- `scripts/verify.py` — offline chain verifier for buyer due-diligence
- `/mnt/archive/audit/README.md` — buyer verification instructions
- UUIDv7 monotonic IDs via `uuid-utils` package; falls back to uuid1
- Intel bus keys: `intel:audit_chain_entry` (TTL 300s), `intel:audit_batch_complete` (TTL 86400s)
- 66 new pure tests → **752 total passing**

### Added — Step 40: SEC EDGAR Direct Pipeline
- `scrapers/edgar/edgar_harvester.py` — eliminates $49/mo sec-api.io dependency
- Three APScheduler jobs: filings (10 min), Form 4 insider (30 min), XBRL fundamentals (daily 06:00 UTC)
- New tables: `edgar_fundamentals`, `edgar_filings_log`
- Redis dedup keys: `edgar:{prefix}:seen:{accession}` (7-day TTL)
- Intel keys: `intel:edgar_filing`, `intel:edgar_insider`
- 38 tests; migration `20260314130000_add_edgar_tables.sql`

### Added — Step 42: Advanced Testing
- Hypothesis property-based tests for risk engine + signal detectors
- VCR.py cassettes for external API responses (CI-safe, no live calls)
- pytest-xdist parallel test execution; pytest-timeout guards

### Added — Step 48: Data Pipeline Resilience
- `core/resilience.py` — circuit breaker, retry decorator, dead-letter queue, resilient HTTP client
- All scrapers and harvesters wrapped with resilience stack

### Fixed
- `FractionalKelly.calculate()`: `min(self.fraction, round(...))` prevents rounding above fraction cap
- `tests/test_api_fuzz.py`: updated to `schemathesis.openapi.from_url()` (schemathesis 4.12 API)

### Infrastructure
- Installed `opentimestamps-client` v0.7.2 — `ots` binary now available at `/usr/local/bin/ots`
- Per-service CLAUDE.md added for: `ems/`, `Kalshi by Cemini/app/`, `Kalshi by Cemini/ems/`, `ui/`, `scrapers/edgar/`

---

## [Mar 13, 2026]

### Added — Step 35 ext: Observability Stack (LGTM + CAGG + AOF + Alertmanager)
- Prometheus, Loki, Grafana Alloy, Grafana Tempo deployed (26 total containers)
- Redis AOF persistence; `config/redis.conf` volume-mounted
- TimescaleDB: `raw_market_ticks` hypertable; `market_ticks_1min` CAGG (1-min)
- Alertmanager v0.27.0; 8 alert rules in 2 groups
- Grafana: Alertmanager datasource + `cemini-overview.json` dashboard

### Added — Step 39: FRED Macro Data Monitor
- `scrapers/fred_monitor.py` — 12 FRED series polled every 900s
- Handles `"."` sentinel value for missing observations (converts to NULL)
- Redis TTL = 1800s (2× poll interval per LESSONS.md pattern)

---

## [Mar 8, 2026]

### Added — Step 29: Vector DB Intelligence Layer
- `intelligence/` package — pgvector + TimescaleDB HNSW semantic search
- CRAG retrieval grading: RELEVANT / AMBIGUOUS / IRRELEVANT
- Embedding: all-MiniLM-L6-v2 (384-dim), lazy singleton
- Realtime worker: subscribes Redis `intel:*`, batches 32 msgs

---

## [Mar 7, 2026]

### Added — Step 26.1: Opportunity Discovery Engine (port 8003)
- `opportunity_screener/` — entity extractor, conviction scorer, Bayesian LR updates
- Dynamic watchlist: 50 tickers, polls `intel:*` every 30s

### Added — Step 21: Cemini SKILL.md
- Transferable architecture package; passes `vet_skill.py`

### Added — Step 4: Kalshi Rewards Scanner
- `scripts/kalshi_rewards.py` — weekly cron; Discord alerts on reward changes

### Added — Step 3: Performance Dashboard (Streamlit, port 8501)
- `ui/performance.py` — 5 tabs: Regime / Signals / P&L / Risk / Health

### Added — Step 34: DevOps Hardening
- Ruff replaces flake8 + bandit; `ruff.toml` at repo root
- Trivy FS scan in CI; Semgrep with 4 custom rules
- `@beartype` on 23 critical functions
- Docker Swarm `deploy:` blocks on all services; Portainer CE

### Added — Step 38: Schema Migrations (dbmate 2.31.0)
- `db/migrations/` — baseline SQL + pgvector + audit tables
- `db/schema.sql` generated via dbmate dump

---

## [Mar 6, 2026]

### Added — Step 27: MCP Intelligence Server (port 8002)
- `cemini_mcp/` — FastMCP 3.1.0; 10 read-only intel tools

### Added — Step 28: Pydantic Data Contracts
- `cemini_contracts/` — 10 modules; `safe_validate` / `safe_dump` at all Intel Bus boundaries

### Added — Step 30: Logit Jump-Diffusion Pricing
- `logit_pricing/` — transforms, indicators, jump-diffusion, precision, pricing engine

### Added — Step 33: Safety Guards
- `SOCIAL_ALPHA_LIVE=true` required for live social signals (C5)
- `WEATHER_ALPHA_LIVE=true` required for live weather signals (C7)
- Postgres password from `POSTGRES_PASSWORD` env (C4)

---

## [Mar 2, 2026]

### Fixed — Regime Gate
- `analyzer.py` publishes Intel Bus every 4 min (was: hourly publish / 5-min TTL mismatch)
- `sniper` strategy_mode → `intel:spy_trend = "bullish"` (extreme fear is contrarian)
- `intel:vix_level = 45.0` when FGI=10

### Added — Step 24: Visual Crossing Weather
- Visual Crossing as 5th weather source; agricultural metrics (GDD, HDD, CDD)

---

## [Mar 1, 2026]

### Added
- Step 2: Docker network segmentation (edge_net / app_net / data_net)
- Step 14: GDELT Geopolitical Harvester
- Step 15: Auto-Documentation CI (`[skip ci]` commits)
- Step 16: Kalshi WebSocket feed
- Step 20: Skill Vetting Protocol

---

## [Feb 28, 2026]

### Added — Step 1: CI/CD Hardening
- GitHub Actions: lint → pip-audit → TruffleHog → deploy pipeline
- `idle_in_transaction_session_timeout = 1min` on Postgres

### Fixed — Data Pipeline
- `ORDER BY created_at` instead of `timestamp` for Polygon free-tier data

---

## [Feb 26, 2026]

### Added — Step 6: Equity Tick Data
- Polygon.io REST ingestion: 23 equity ETFs + 7 crypto symbols
- TimescaleDB `raw_market_ticks` table
