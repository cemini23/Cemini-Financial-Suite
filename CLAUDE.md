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
- Linter: **Ruff** (ruff.toml, replaces flake8+bandit). Run: `ruff check .` — must exit 0
  - line-length=120, select E,W,F,B,S,ASYNC,UP,I,N,SIM
  - E741 (single-letter vars l/O/I) enforced — rename to ln/val/idx
- Security scanning: Trivy (FS scan in CI, image scan via `scripts/trivy-scan.sh` on server)
- Static analysis: Semgrep (`.semgrep/` custom rules + p/trailofbits via CI)
- Runtime types: `@beartype` on all EMS, intel_bus, risk_engine, macro_regime functions
- Schema migrations: **dbmate** (`dbmate up` before new DB features; migrations in `db/migrations/`)
- All pre-gate data quarantined at `/opt/cemini/archives/data_quarantine/` — do NOT use
- Do NOT disrupt running harvesters or playbook_runner
- C4: Postgres password reads from `POSTGRES_PASSWORD` env var (never hardcode)
- C5: `SOCIAL_ALPHA_LIVE=true` required for live social signals (default: gated/neutral)
- C7: `WEATHER_ALPHA_LIVE=true` required for live weather signals (default: gated/neutral)
- C1 RESOLVED (Mar 14): `ENABLE_BRAIN_PUBLISH=true` activates orchestrator → Redis publish
- C3 RESOLVED (Mar 14): Mac path in verify_install.py → `QUANTOS_ROOT` env var + `__file__` fallback
- L3 RESOLVED (Mar 14): `HARD_BLOCK_EXPOSURE=true` env var hard-blocks on exposure breach (default: observe)
- L4 RESOLVED (Mar 14): strategy_mode now regime-driven from `intel:playbook_snapshot`
- A4 RESOLVED (Mar 14): BQ_TABLE_ID defaults both `market_ticks` (already consistent)
- A6 RESOLVED (Mar 14): QuantOS `executed_trades` Redis-backed (24h TTL, hydrate on startup)
- S5 RESOLVED (Mar 14): No duplicate ib_insync imports found in router.py

## Networks

| Network | Services |
|---------|---------|
| edge_net | nginx, cloudflared |
| app_net | brain, analyzer, ems, quantos, kalshi, playbook, cemini_os |
| data_net | postgres, redis, pgadmin |

## Completed Steps

Steps 1 (CI/CD), 2 (Docker Networks), 3 (Performance Dashboard), 4 (Kalshi Rewards),
6 (Equity Ticks), 14 (GDELT), 15 (Auto-Docs), 16 (Kalshi WS), 20 (Skill Vetting),
21 (SKILL.md), 24 (Visual Crossing Weather), 26 (Opportunity Discovery), 27 (MCP Server),
28 (Pydantic Contracts), 29 (Vector DB), 30 (Logit Pricing), 32 (CLAUDE.md),
33 (Safety Guards C4+C5+C7), 34 (DevOps Hardening), 35 (LGTM Observability),
38 (Schema Migrations), 39 (FRED Monitor), 40 (SEC EDGAR), 41 (IP Sale Docs),
42 (Advanced Testing), 43 (Cryptographic Audit Trail), 48 (Data Pipeline Resilience),
50 (Polars Feature Engineering), 51 (License Compliance & Virtual Data Room).

## Step 41: IP Sale Documentation Site

- **Config**: `mkdocs.yml` at project root — MkDocs-Material theme, mermaid2 plugin
- **Docs**: `docs/` — 36 pages across architecture, engines, intelligence, data-sources, verification, QA, infrastructure, appendices
- **Build**: `mkdocs build --strict` (passes zero warnings); output in `site/`
- **Serve locally**: `mkdocs serve` (port 8000)
- **Tests**: `tests/test_docs.py` — 24 pure filesystem tests
- **Missing pages that were added**: verification/opentimestamps.md, qa/{test-suite,hypothesis,schemathesis,mutmut,ci-cd}.md, infrastructure/{devops,observability,migrations,resilience}.md, appendices/{licenses,tech-debt,glossary}.md
- **License inventory**: `docs/appendices/licenses.md` — generated via `pip-licenses --format=markdown`
- **YAML safe_load pitfall**: mkdocs.yml contains `!!python/name:` tags — use text-based checks in tests (not `yaml.safe_load`)

## Step 43: Cryptographic Audit Trail

- **Layer 1**: SHA-256 hash chain — `shared/audit_trail/` package + PL/pgSQL BEFORE INSERT trigger
  - Tables: `audit_hash_chain`, `audit_batch_commitments`, `audit_intent_log`
  - Migration: `db/migrations/20260314200000_create_audit_hash_chain.sql`
  - JSONL mirror: `/mnt/archive/audit/chains/YYYY-MM-DD.jsonl`
- **Layer 2**: pymerkle daily Merkle tree at 23:55 UTC (APScheduler cron)
  - Batch output: `/mnt/archive/audit/batches/YYYY-MM-DD/batches.json`
- **Layer 3**: OpenTimestamps best-effort (`ots` binary not installed on server — skips gracefully)
- **VCP Silver Tier** naming conventions: `entry_id`, `commitment_id`, `chain_hash`, `merkle_root`
- **UUIDv7** monotonic IDs (uuid-utils package) on all audit entries
- **Intent logging**: `signal_catalog.py:scan_symbol()` logs pre-evaluation intent BEFORE detect()
- **Offline verifier**: `scripts/verify.py --archive-root /mnt/archive/audit/`
- **Intel Bus**: `intel:audit_chain_entry` (TTL 300s), `intel:audit_batch_complete` (TTL 86400s)
- **Fail-silent**: all audit writes are non-blocking, never crash the caller
- **JSON canon**: `json.dumps(sort_keys=True, separators=(',',':'))` everywhere
- **Archive README**: `/mnt/archive/audit/README.md` — buyer verification instructions
- **Env var**: `AUDIT_ARCHIVE_DIR` (default `/mnt/archive/audit`) — read at call time (not import time)

## Step 51: License Compliance & Virtual Data Room

- **SBOM**: `scripts/license_audit.py` → `vdr/02_sbom.md`, `vdr/03_license_flags.json`, `vdr/04_isolation_report.md`
  - pip-licenses binary at `/usr/local/bin/pip-licenses` uses `/usr/bin/python3` (3.10) shebang — use `shutil.which("pip-licenses")` not `sys.executable -m pip_licenses`
  - Green/Yellow/Red classification: Yellow check BEFORE Red (LGPL contains 'gpl' substring)
  - 297 total packages: 273 Green, 13 Yellow, 11 Red (as of Mar 14, 2026)
  - Known flags hand-curated in `KNOWN_FLAGS` dict: pymerkle (Red), psycopg2-binary/opentimestamps/chardet/semgrep (Yellow)
- **CVE scan**: `scripts/cve_audit.py` → `vdr/05_cve_report.md`
  - pip-audit binary at `/usr/local/bin/pip-audit` — use `shutil.which("pip-audit")` not `sys.executable -m pip_audit`
  - 32 vulnerabilities found (system packages + dev tools); focus on production requirements.txt for real risk
  - cryptography 3.4.8 is the main production concern — upgrade to 42+ resolves all CVEs
- **Authorship**: `scripts/authorship_proof.py` → `vdr/06_authorship_proof.md`, `vdr/07_git_stats.json`
  - 76 human commits by Cemini23 + 28 bot commits by github-actions[bot]
  - Filter bots by checking for `[bot]` in author name
  - Section 1235 statement in authorship proof — informational only, not legal advice
- **VDR**: `vdr/` directory with 13 files (README + 01-12)
  - Static files: README, 01, 08, 09, 10, 11, 12
  - Generated files: 02, 03, 04, 05, 06, 07 (re-run `python3 scripts/generate_vdr.py`)
- **MkDocs**: Due Diligence section added (4 pages under `docs/due-diligence/`)
  - `mkdocs build --strict` passes with 0 warnings
- **Tests**: `tests/test_vdr.py` — 26 pure filesystem tests

## Step 50: Polars Feature Engineering

- Package: `shared/feature_engine/` — 7 modules
- FEATURE_VECTOR_DIM = 18 features (momentum + volatility + participation + sentiment + macro + regime + price)
- RSI: Wilder SMMA (alpha=1/period, span=2*period-1) — NOT SMA
- DB fallback: connectorx → adbc → psycopg2
- No Pandas in feature_engine — pure Polars only
- orjson_response.py: FastAPI drop-in, do NOT retrofit existing endpoints
- Tests: tests/test_feature_engine.py

## Testing

- All tests in `/opt/cemini/tests/` — pure, no network/Redis/Postgres
- Run: `pytest tests/ -v && ruff check .`
- Current count: 845 tests passing (37 new in test_feature_engine.py for Step 50), ruff clean

## Token Efficiency
Always use RTK (installed globally) to compress verbose CLI output before sending to context.
RTK reduces directory trees, error logs, git diffs, and JSON payloads by 60-90%.

## Roadmap Auto-Update Rule

**MANDATORY on every step commit:** Update `docs/ROADMAP.md` to reflect:
1. Step status change (READY → ✓ DONE with date and commit hash)
2. New test count and failure count in header Progress line
3. Any new Known Issues resolved or discovered
4. Maintenance Log entry: date, step name, commit hash, test count delta
5. Update "Progress" line in header (X of 51 steps, N tests, N failures)

`docs/ROADMAP.md` is the canonical roadmap. The Google Doc is deprecated.
Do NOT skip this update — it is part of the Definition of Done for every step.
