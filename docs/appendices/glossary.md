# Glossary

Key terms and abbreviations used throughout the Cemini Financial Suite documentation
and codebase.

---

## A

**APScheduler**
Advanced Python Scheduler — used to schedule recurring harvester jobs with deterministic
timing. Supports cron triggers (daily) and interval triggers (every N seconds/minutes).

**ATR (Average True Range)**
A volatility indicator measuring the average range of price bars over N periods.
Used in signal detection (ElephantBar: range > 2×ATR) and stop-loss placement.

**Aiobreaker**
Python library providing async circuit breaker functionality. Used in all async
data harvesters to prevent cascading failures when external APIs are unavailable.

---

## B

**beartype**
Python runtime type-checking library. Decorating a function with `@beartype` causes
type annotations to be enforced at call time, raising `BeartypeCallHintParamViolation`
on mismatches. Applied to 23 critical functions.

**Brain**
The root orchestrator service — a LangGraph-based agent that reads Intel Bus signals,
runs a CIO debate, and publishes trade verdicts. Currently in paper-trading mode.
See [Root Orchestrator](../engines/orchestrator.md).

---

## C

**CAGG (Continuous Aggregate)**
TimescaleDB feature that maintains a materialized view (e.g., 1-minute OHLCV bars)
that is automatically refreshed as new data arrives. Used for `market_ticks_1min`.

**Circuit Breaker**
A resilience pattern that stops sending requests to a failing service after N
consecutive errors, "opening" the circuit. After a timeout, it enters "half-open"
state and allows one probe request. If the probe succeeds, the circuit closes.

**CVaR (Conditional Value-at-Risk)**
Also called Expected Shortfall. The mean of returns in the worst X% tail (Cemini uses
99th percentile). More conservative than plain VaR — it asks "given that we're in the
worst 1% of outcomes, what is the expected loss?"

---

## D

**Dead-Letter Queue (DLQ)**
Storage for events that failed all retry attempts. Cemini writes dead-letter events
to both Redis (`intel_dead_letters` list) and Postgres (`intel_dead_letters` table)
for later replay or audit.

**dbmate**
SQL-first database migration tool. Migrations are plain `.sql` files in `db/migrations/`.
Run `dbmate up` to apply pending migrations.

**DSoR (Directional Signal of Regime)**
Internal term for the signal-direction modifier applied by the macro regime gate.
GREEN regime allows LONG signals; RED regime restricts to shorts or cash.

---

## E

**EDGAR**
Electronic Data Gathering, Analysis, and Retrieval — the SEC's public filing system.
Cemini scrapes EDGAR directly (no third-party API) for Form 4 insider filings, XBRL
fundamentals, and all company filings.

**EMS (Execution Management System)**
The order routing layer. Routes trade verdicts from the Brain to the appropriate
broker adapter (Kalshi autopilot, QuantOS). Currently in paper-trading mode.

**EpisodicPivot**
A technical pattern detector. Identifies sudden high-volume breakouts above a 20-bar
resistance level, signaling potential institutional accumulation.

---

## F

**FRED (Federal Reserve Economic Data)**
Macroeconomic time series database maintained by the St. Louis Federal Reserve.
Cemini pulls 8 series (unemployment, CPI, 10Y yield, etc.) daily via the FRED API.

**FractionalKelly**
Position sizing formula. Full Kelly × fraction (default 25%). Limits position size
to a fraction of the mathematically optimal bet to reduce variance and model error.

---

## G

**GDELT (Global Database of Events, Language, and Tone)**
A realtime database of global news and events. Cemini scrapes GDELT for geopolitical
risk signals that may affect market sentiment.

**GREEN / YELLOW / RED**
The three states of the Macro Regime Classifier:
- **GREEN**: SPY above rising 21-day EMA → full strategy activation
- **YELLOW**: SPY below 21 EMA but above 50 SMA → defensive, no new longs
- **RED**: SPY below 50 SMA → survival mode, cash or short only

---

## H

**Hash Chain**
A cryptographic structure where each record's hash includes the hash of the previous
record. Tampering with any record invalidates all subsequent hashes, making the chain
tamper-evident.

**Hishel**
RFC 7234-compliant HTTP caching library for httpx. Stores cached responses in SQLite
per service. Reduces redundant API calls and provides offline degradation.

**HighTightFlag**
A technical pattern. A stock that doubles in ≤8 weeks, then consolidates in a tight
flag pattern (depth < 20%), followed by a volume-expansion breakout.

**HNSW (Hierarchical Navigable Small World)**
An approximate nearest-neighbor index algorithm used by pgvector for semantic search.
Cemini uses `m=16, ef_construction=200` for the `intel_embeddings` table.

---

## I

**InsideBar212**
A 3-bar compression pattern: wide outside bar (2) → narrow inside bar (1) → breakout
bar (2). Signals a volatility squeeze followed by directional resolution.

**Intel Bus**
The Redis-backed intelligence sharing layer. All services publish and consume on
`intel:*` channels. No direct HTTP calls between services — only Redis pub/sub.

---

## J

**JNK/TLT Cross-Validation**
A macro regime confirmation check. JNK = HYG/JNK high-yield credit ETF; TLT = 20Y
Treasury bond ETF. If JNK underperforms TLT during an equity breakout, the signal is
flagged as potentially suspect (credit markets not confirming equity strength).

---

## K

**Kalshi**
A regulated prediction market exchange. Cemini trades binary event contracts on Kalshi
via the Kalshi by Cemini engine (FastAPI :8000).

**Kelly Criterion**
A mathematical formula for optimal bet sizing: `W - (1-W)/R` where W = win rate and
R = reward-to-risk ratio. Cemini applies a 25% fractional Kelly to reduce variance.

**Kill Switch**
A safety mechanism that halts all trading and broadcasts `CANCEL_ALL` when any of five
conditions are met: PnL velocity breach, order rate anomaly, exchange latency spike,
price deviation, or master kill trigger.

---

## L

**LangGraph**
A Python framework for building stateful, multi-step LLM agent graphs. Used in the
Brain orchestrator for the CIO debate multi-agent pattern.

**LGTM Stack**
Grafana's observability stack: Loki (logs), Grafana (dashboards), Tempo (traces),
Metrics (Prometheus). Deployed in Step 35.

**Logit Pricing**
The platform's options/contract pricing engine (`logit_pricing/` package). Applies
logit-space transformations, jump-diffusion models, and CVaR precision to price
binary event contracts.

---

## M

**MAPPO (Multi-Agent PPO)**
Multi-Agent Proximal Policy Optimization — a reinforcement learning algorithm planned
for future steps. The PlaybookLogger's logging infrastructure is designed to generate
training data for future MAPPO training runs.

**Merkle Tree**
A binary tree where each non-leaf node is the hash of its child nodes. The root hash
commits to all leaf values. Used in Layer 2 of the Audit Trail for daily batch
commitments.

**MomentumBurst**
A technical pattern detecting sustained multi-bar momentum: 3+ consecutive higher
closes with positive volume regression slope and RSI below 80 (not overbought).

---

## O

**OpenTimestamps (OTS)**
A protocol for proving data existed at a specific time by committing its hash to the
Bitcoin blockchain. The `.ots` proof file verifies with `ots verify`. Used in Layer 3
of the Audit Trail.

---

## P

**Paper Trading**
Simulation mode — the platform generates signals and logs trades but does not submit
live orders to any exchange. Cemini is currently in paper trading mode.

**pgvector**
PostgreSQL extension for vector similarity search. Used in the Vector DB Intelligence
Layer (Step 29) to store 384-dimensional sentence embeddings for semantic intel retrieval.

**Playbook**
The Trading Playbook — an observation-only regime/signal/risk orchestration layer.
Runs a 5-minute scan loop but never places orders. See [Trading Playbook](../engines/playbook.md).

---

## R

**Regime Gate**
The macro regime classifier that gates all signal processing. Only signals aligned with
the current regime (GREEN/YELLOW/RED) pass through to the risk engine.

**RSI (Relative Strength Index)**
A momentum oscillator measuring the speed and magnitude of recent price changes.
Cemini uses Wilder's SMMA method (industry standard) rather than simple SMA.

**Ruff**
A fast Python linter and formatter that replaces flake8, isort, and bandit.
Configured via `ruff.toml`. Must exit 0 before deploy.

---

## S

**Schemathesis**
API fuzz testing library. Reads OpenAPI schemas and auto-generates adversarial request
payloads to test for 5xx errors, schema violations, and security issues.

**Semgrep**
Static analysis tool with custom rule support. Cemini uses 4 custom rules
(`.semgrep/`) targeting trading-platform-specific anti-patterns.

**Signal Catalog**
The registry of discrete technical pattern detectors. Six detectors: EpisodicPivot,
MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212.

---

## T

**Tenacity**
Python retry library with exponential backoff. Wraps individual HTTP calls in
data harvesters.

**TimescaleDB**
PostgreSQL extension for time-series data. Used for `raw_market_ticks` (hypertable)
and `market_ticks_1min` (continuous aggregate).

**TruffleHog**
Secret scanning tool. Scans git history for verified credentials using entropy analysis
and pattern matching. Runs in CI on every push.

---

## U

**UUIDv7**
A UUID variant that encodes a millisecond-precision timestamp in the most significant
bits, providing monotonic ordering. Used for all audit trail entry IDs.

---

## V

**VCP (Volatility Contraction Pattern)**
Mark Minervini's breakout setup. Three contracting price waves with volume drying up
on the final contraction. Breakout on expanding volume is the entry trigger.

**VCP Silver Tier**
An institutional naming convention for audit trail fields: `entry_id`, `commitment_id`,
`chain_hash`, `merkle_root`. Compliance signals institutional-grade data governance.

---

## W

**Weinstein Stage Analysis**
Stan Weinstein's market cycle framework: Stage 1 (base), Stage 2 (uptrend), Stage 3
(top), Stage 4 (decline). HighTightFlag detector checks for Stage 2 characteristics.

---

## X

**XBRL (eXtensible Business Reporting Language)**
A standard for encoding financial statements. SEC EDGAR provides XBRL filings for
company fundamentals. Cemini's EDGAR pipeline parses XBRL for revenue, EPS, and
other fundamental data.
