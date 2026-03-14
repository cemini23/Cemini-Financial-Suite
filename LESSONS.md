# Cemini Financial Suite — Hard-Won Lessons

Persistent file. Every Claude Code session reads this on startup.
Append new entries when you discover a pattern that cost debugging time.
Format: category | mistake | fix | file(s) affected.

---

## Data Pipeline

**Polygon timestamp ordering**
Mistake: ORDER BY timestamp on free-tier Polygon data.
Fix: ORDER BY created_at instead. Free-tier bar close times can be hours behind real time.
Files: 4 files fixed Feb 28.

**Redis TTL mismatch**
Mistake: intel:spy_trend published hourly but had 5-min TTL → brain got nil 55/60 min.
Fix: Always match publish frequency to TTL. analyzer.py now publishes Intel Bus every 4 min.
Commit: fb8e1d6 (Mar 2).

---

## Financial Math

**RSI calculation (FIXED — Desloppify Mar 8)**
QuantBrain.calculate_rsi() now uses Wilder's SMMA (industry standard).
Seeds with SMA on first `period` deltas, then smooths: avg = (prev*(period-1)+current)/period.
Matches pandas-ta, TradingView, Wilder 1978. No downstream tests depend on old SMA-RSI.

**Logit-space precision**
Enforce multiplication-before-division in pricing formulas.
Use Decimal type for intermediate calculations. Assert guards for NaN/Inf.

---

## Docker / Infrastructure

**idle_in_transaction_session_timeout**
Set to 1min on Postgres. Without this, leaked connections from crashed containers hold locks.
Fixed Feb 28.

**fresh_start_pending (RESOLVED — Desloppify Mar 8)**
Now Redis-backed: quantos:fresh_start_requested key. Only fires when explicitly set to "true".
Use QuantOS/scripts/trigger_fresh_start.py to request a liquidation.
Normal restarts do NOT trigger liquidation.

**Container filesystem**
Containers cannot access host .env unless explicitly volume-mounted.
Single-file bind mounts: edits on host create new inode, container sees old one until restart.

**Docker network segmentation (Step 2)**
edge_net / app_net / data_net. Services on different nets cannot talk directly.
kalshi_autopilot needs both app_net AND data_net.

---

## Redis Patterns

**Auth required**
Always use REDIS_PASSWORD env var. Unauthenticated connections fail silently.

**intel: namespace**
All cross-system intelligence uses this prefix. Never publish to bare channel names.

**BigQuery table mismatch (RESOLVED)**
Both DataHarvester and CloudSignalEngine now use BQ_TABLE_ID env var defaulting to "market_ticks".
Both log the table name at startup. LESSONS.md entry was outdated from an older version.

---

## CI/CD

**Linter: Ruff (replaces flake8 + bandit as of Step 34)**
Run `ruff check .` — must exit 0 in CI. Config: ruff.toml (line-length=120).
E741 (ambiguous var names l/O/I) enforced — rename to ln/val/idx.
E221/E272 (aligned spacing) NOT ignored — avoid dict alignment formatting.
Trivy (FS scan CI) and Semgrep (custom rules + p/trailofbits) run as informational jobs.

**Auto-docs infinite loop**
generate_docs.py commits trigger CI → triggers generate_docs.py.
Prevented by [skip ci] in commit message. Do NOT remove [skip ci] from auto-doc commits.

---

## Engagement Scoring (X Harvester)

**Normalized scores need floor gates**
Accounts with near-zero followers get artificially inflated normalized engagement.
Min 500 followers + min 10 raw engagement before normalized component activates.
Blended rank: 40% raw, 60% normalized. (Already in x_harvester.py _generate_sprint_summary)

---

## Safety Guards (Step 33 — Mar 6)

**SOCIAL_ALPHA_LIVE guard (C5)**
social_alpha/analyzer.py get_target_sentiment() returns score=0/NEUTRAL if env var != "true".
Prevents simulated/unreliable tweet sentiment from influencing live Kalshi trades.

**WEATHER_ALPHA_LIVE guard (C7)**
weather_alpha/analyzer.py analyze_market() returns no opportunities if env var != "true".
Prevents weather signal from trading when data quality is not confirmed live.

**C4: No hardcoded DB passwords**
All Postgres connections use os.getenv('POSTGRES_PASSWORD', 'quest').
Never commit password literals.

---

## Regime Gate (Mar 2)

**"sniper" strategy_mode → spy_trend "neutral" not "bearish"**
Extreme fear (FGI=10, VIX=45) is contrarian signal → bullish, not bearish.
intel:vix_level = 45.0 when FGI=10. intel:spy_trend = "bullish" in sniper mode.

---

## DevOps Hardening (Step 34 — Mar 7)

**Ruff migration: 1911 violations → carry forward as ignores**
Start with `ruff check . --select ALL` to count scope, then build migration-safe ignore list
preserving old flake8 suppressions. Only fix genuine B-rule bugs (B006 mutable defaults,
B904 exception chaining, B008 FastAPI Body calls). Unknown flake8 codes (E127, E128) don't
exist in ruff — remove them.

**Semgrep path patterns: v2 requires `**/ ` prefix**
`tests/**` → `**/tests/**` in semgrepignore v2. Otherwise no files are excluded.
Same applies to include paths in custom rules.

**beartype: int is not a subtype of float**
PEP 484 numeric tower is NOT enforced by beartype. `nav: float` rejects int literals.
Use `nav: float | int` union for any parameter that could be an int.
`@staticmethod` must come before `@beartype` in the decorator stack.

**Docker Swarm: profiles not supported → deploy.replicas: 0**
Swarm silently ignores `profiles:`. Keep `profiles:` for compose compatibility AND add
`deploy.replicas: 0` as Swarm-native gate for optional services.

**Network driver: remove explicit bridge for Swarm compatibility**
Swarm requires overlay networks. Remove `driver: bridge` from compose network defs and add
`attachable: true`. Compose defaults to bridge, Swarm defaults to overlay — both work.

**Portainer: --base-url not --basepath**
Portainer CE flag is `--base-url /portainer`, not `--basepath`. nginx location /portainer/
must proxy_pass to portainer:9000/portainer/ (preserving the prefix).

---

## Schema Migrations (Step 38 — Mar 7)

**dbmate: atomically rolls back on any error**
If any statement in a migration fails, the whole migration is rolled back. `dbmate status`
shows it as `[ ]` pending even if prior statements succeeded. Always verify after `dbmate up`.

**dbmate dump requires pg_dump matching server version**
pg_dump v14 rejects PG 16 server. Options: install postgresql-client-16 (if available in apt),
or create a shell wrapper at `/usr/local/bin/pg_dump` that calls `docker exec postgres pg_dump`.

**CREATE OR REPLACE VIEW cannot rename columns**
If an existing view has different column names, `CREATE OR REPLACE VIEW` fails.
Use `DROP VIEW IF EXISTS` + `CREATE VIEW` instead.

**postgres container IP for CLI tools**
Port 5432 is exposed within the Docker network only (not mapped to host).
Use container IP (e.g. 172.19.0.3) for CLI tools like dbmate run outside containers.
Find IP: `docker inspect postgres | grep '"IPAddress"'`

**dbmate one-shot in docker-compose**
Use `restart_policy: condition: none` for migration containers so they don't restart
after completing. In compose mode the container exits; in Swarm it stops (desired state).

---

## Desloppify Pass (Mar 8, 2026)

**D1: KALSHI_CONFIG_DIR env var**
KalshiAdapter now logs WARNING if neither KALSHI_CONFIG_DIR nor KALSHI_SUITE_PATH is set.
Both env vars accepted; KALSHI_CONFIG_DIR takes priority.

**D2: KalshiRESTAdapter.get_buying_power() fallback**
Returns _BUYING_POWER_FALLBACK ($1000) with WARNING log on API failure, not 0.0.
Prevents $0 buying power from zeroing out position sizing during Kalshi downtime.

**D6: Redis TTL for dedup state**
autopilot.py _save_state() now sets ex=604800 (7 days) on kalshi:executed_trades and kalshi:blacklist.
Prevents unbounded Redis growth. Keys expire after 7 days automatically.

**D7: strategy_mode regime gate**
analyzer.py now reads intel:playbook_snapshot before setting strategy_mode.
RED regime → always "conservative". YELLOW regime → cap at "conservative" (never "aggressive").
GREEN → win-rate-based as before. Logs the regime-aware decision.

**D8: Wilder's SMMA RSI**
QuantBrain.calculate_rsi() now uses correct Wilder smoothing. See Financial Math above.

**D9: Semgrep triage**
138 total findings. 4 fixed (hardcoded passwords). 7 suppressed with inline comments.
127 accepted (88 float-for-money false positives + 39 credential defaults).
See SECURITY_NOTES.md for full breakdown.

**D11: cemini_version.py**
Single source of truth at /opt/cemini/cemini_version.py.
SERVICE_VERSIONS dict for per-service versions. TradingEngine imports from it.

**D12: Duplicate import removed**
ibkr.py submit_order_by_quantity() had `from ib_insync import Stock, MarketOrder, LimitOrder`
inside method body duplicating the module-level import. Removed.

**D14: KalshiREST class naming**
Added docstrings distinguishing KalshiRESTv2 (raw client, ems/kalshi_rest.py)
from KalshiRESTAdapter (BaseExecutionAdapter, core/ems/adapters/kalshi_rest.py).

**Hardcoded passwords fixed**
macro_harvester.py, social_scraper.py, signal_generator.py, scripts/archive_logs.py
All now use os.getenv("POSTGRES_PASSWORD", "quest") pattern consistently.

**Containers that need restart after this pass:**
- `coach_analyzer` — analyzer.py changed (D7, D13, D10 type annotations)
- `quantos_brain` (if running) — brain.py RSI fix (D8) requires image rebuild
- No other services touched in ways that affect running behavior.

---

## FRED API (Step 39)

**FRED sentinel value**
FRED returns the string `"."` (a literal dot) for missing or unreported observations — NOT Python None or JSON null.
Always call `_parse_fred_value()` which converts `"."` → `None`. Storing None as NULL in Postgres is correct.
Files: scrapers/fred_monitor.py

**FRED rate limit**
Free tier allows 120 requests/minute. With 12 series per poll cycle, use 0.6s sleep between calls to stay conservative.
Do NOT batch all 12 calls without sleeping — FRED will return 429s.

**FRED monthly series are not stale**
UNRATE, PAYEMS, PCEPI, CPILFESL, UMCSENT update monthly. Do not raise staleness alerts for these series.
Weekly series: ICSA, WALCL. Daily: T10Y2Y, T10Y3M, DFF, BAMLH0A0HYM2, VIXCLS.

**FRED TTL must be >= 2× poll interval**
fred_monitor polls every 900s. Redis TTL must be >= 1800s.
IntelPublisher.publish() hardcodes TTL=300 — use Redis SET directly with ex=FRED_TTL for fred_monitor.
This follows the same LESSONS.md Redis TTL mismatch pattern (see: analyzer.py fix, commit fb8e1d6).

---

## Advanced Testing (Step 42)

**Hypothesis with Pydantic v2 — use st.builds() or explicit st.floats()**
st.builds(MyModel) works but requires all fields to have defaults or explicit strategies.
Safer: provide explicit strategies via @given(field=st.floats(...)) and construct manually.
Avoid NaN/Inf in Hypothesis floats — use allow_nan=False, allow_infinity=False.

**Hypothesis HealthCheck.too_slow**
Suppress with @settings(suppress_health_check=[HealthCheck.too_slow]) for tests
that build DataFrames or run signal detectors. Otherwise Hypothesis aborts after ~0.2s setup.

**mutmut: target specific files, not full codebase**
Full-codebase mutation runs take hours. Use --paths-to-mutate for surgical targeting.
See mutmut_config.py pre_mutation() hook for the allow-list.

**VCR.py: record_mode='none' in CI**
Never commit cassettes with real API keys. _scrub_request() in conftest.py strips
api_key= query params before saving. Set VCR_RECORD_MODE=new_episodes locally to record.

**pytest-xdist: -n auto requires stateless tests**
Tests run in separate worker processes — no shared mutable module state.
If a test fails with -n auto but passes serially, check for global state mutation
or file path conflicts. Use tmp_path fixture for temp files.

**pytest --timeout requires pytest-timeout**
Add pytest-timeout to requirements. CI install: pip install pytest-timeout.
Without it, --timeout flag causes "unrecognized arguments" error.

---

## Cryptographic Audit Trail (Step 43)

**Module-level env var constants break test patching**
Mistake: `ARCHIVE_ROOT = os.getenv("AUDIT_ARCHIVE_DIR", "/mnt/archive/audit")` at module level.
Fix: use `def _archive_root(): return os.getenv(...)` at call time. Otherwise `patch.dict(os.environ, ...)`
in tests has no effect — the constant is already baked in at import time.
Files: shared/audit_trail/chain_writer.py, intent_logger.py, merkle_batch.py

**uuid-utils: always import stdlib uuid for fallback**
If uuid-utils is installed, `import uuid as _uuid_std` inside the except block won't run.
Tests that mock `_UUID7_AVAILABLE = False` then get NameError on `_uuid_std`.
Fix: always `import uuid as _uuid_std` at module top, before the try/except.
File: shared/audit_trail/chain_writer.py

**pymerkle InmemoryTree.append_entry() takes bytes**
Pass `payload_hash.encode("utf-8")` not the raw str. The tree hashes the bytes directly.
`get_state()` returns 32 bytes — call `.hex()` for the 64-char hex string.

**PL/pgSQL dollar-quoting: use $$ not $**
Single `$` inside a function body causes parse errors. Use `$$` as the delimiter.
Standard pattern: `CREATE OR REPLACE FUNCTION ... AS $$ ... $$ LANGUAGE plpgsql;`

**PL/pgSQL sha256() returns bytea**
`sha256(text::bytea)` returns bytea. Wrap with `encode(..., 'hex')` to get TEXT.
Requires PostgreSQL 11+. Available in PG 16 without any extension.

**ChainWriter: trigger computes prev_hash/chain_hash**
The BEFORE INSERT trigger in Postgres overwrites prev_hash and chain_hash.
The Python writer passes GENESIS_HASH as placeholder; trigger replaces both fields.
After INSERT, use a SELECT to fetch the trigger-computed values back for the JSONL mirror.

**OpenTimestamps binary not installed on Hetzner VPS**
`ots` is not in apt/pip by default. All Layer 3 code must use `shutil.which("ots")` guard.
Log INFO (not WARNING) when missing — it's an expected optional dependency.
Files: shared/audit_trail/merkle_batch.py._try_ots_stamp()

---

## MkDocs / Documentation (Step 41)

**yaml.safe_load fails on mkdocs.yml with !!python/name: tags**
Mistake: used `yaml.safe_load()` to parse mkdocs.yml in tests.
Fix: use `text.read_text()` + simple string checks (`"site_name:" in content`).
The `!!python/name:mermaid2.fence_mermaid_custom` tag causes `ConstructorError`.
Files: tests/test_docs.py

**ROADMAP.md in docs/ generates INFO (not a warning)**
MkDocs prints "- ROADMAP.md" when a file is in docs/ but not in nav. This is INFO-level,
not a WARNING. `mkdocs build --strict` does NOT abort for this. Harmless.

**MkDocs Material "MkDocs 2.0" banner is not a build warning**
The red ⚠ banner is a marketing notice from the Material team; it does not affect
`--strict` mode or abort the build. Filter it from output in CI log parsing if noisy.
