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

**RSI calculation**
QuantBrain uses SMA-RSI, not standard Wilder's SMMA-RSI. Known issue.
Do NOT "fix" without explicit approval — downstream models may depend on current behavior.

**Logit-space precision**
Enforce multiplication-before-division in pricing formulas.
Use Decimal type for intermediate calculations. Assert guards for NaN/Inf.

---

## Docker / Infrastructure

**idle_in_transaction_session_timeout**
Set to 1min on Postgres. Without this, leaked connections from crashed containers hold locks.
Fixed Feb 28.

**fresh_start_pending**
Set True on every QuantOS restart, forces liquidation of all positions.
By design in paper mode but WILL be dangerous in live trading (Step 10).

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

**BigQuery table mismatch**
DataHarvester writes market_data, CloudSignalEngine reads market_ticks.
Do not create new tables to "fix" without a migration plan.

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
