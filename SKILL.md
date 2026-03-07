---
name: cemini-financial-suite
version: 1.0.0
description: Algorithmic trading platform with three cooperating engines sharing intelligence via Redis pub/sub
author: Cemini
domain: financial-trading
prerequisites: Docker, docker-compose, Python 3.11+, Redis, PostgreSQL/TimescaleDB
---

# Cemini Financial Suite — Agent Skill

This is a **transferable agent skill**. Load this file and you have the domain expertise
to navigate, modify, and extend the Cemini codebase without re-explanation.

**What this is not:** A copy of service-level CLAUDE.md files. Those cover single-service
mechanics. This file gives you the intelligence to make cross-cutting architectural decisions.

---

## 1. System Overview

Cemini is a private-use algorithmic trading platform running on a single Hetzner VPS
(Ubuntu 24, Docker Compose, 20 active containers). It operates three cooperating engines:
a Root orchestrator (brain + analyzer + EMS) for equities/crypto, QuantOS (FastAPI :8001)
for stock and crypto signals, and Kalshi by Cemini (FastAPI :8000) for prediction markets.
All three share intelligence through a Redis pub/sub bus using the `intel:*` namespace.
The architecture paradigm is **intelligence-in, ticker-out**: the system autonomously
discovers opportunities from multi-source intelligence rather than scanning a static watchlist.
An MCP server (port 8002) exposes live intel as typed read-only tools for external AI agents.
Pydantic v2 data contracts enforce typed boundaries at every service interface.
The platform is designed for eventual IP sale to prop firms, fintech, or hedge funds.

---

## 2. Service Topology

| Container name | Service key | Networks | Port | Role | CLAUDE.md |
|---|---|---|---|---|---|
| `postgres` | postgres | data_net | 5432 (internal) | TimescaleDB — market ticks, playbook logs, trade history | — |
| `pgadmin` | pgadmin | edge_net, data_net | 80 (internal) | Postgres admin UI | — |
| `redis` | redis | data_net | 6379 (internal) | Intel bus, signal routing, all pub/sub | — |
| `polygon_ingestor` | polygon_feed | app_net, data_net | — | Equity/crypto tick ingestion from Polygon | — |
| `brain` | brain | app_net, data_net | — | LangGraph orchestrator — reads ticks, runs QuantBrain RSI, publishes trade_signals | root CLAUDE.md |
| `coach_analyzer` | analyzer | app_net, data_net | — | Publishes strategy_mode, intel:vix_level, intel:spy_trend, intel:portfolio_heat every 4 min | root CLAUDE.md |
| `scribe_logger` | logger | app_net, data_net | — | Logs signals and events to Postgres; live-mounted from repo | root CLAUDE.md |
| `social_scraper` | social_scraper | app_net, data_net | — | X social sentiment scraper | root CLAUDE.md |
| `macro_scraper` | macro_scraper | app_net, data_net | — | Macro data harvester | root CLAUDE.md |
| `gdelt_harvester` | gdelt_harvester | app_net, data_net | — | GDELT geopolitical risk every 15 min | root CLAUDE.md |
| `kalshi_autopilot` | kalshi_autopilot | app_net, data_net | — | CeminiAutopilot: runs all 5 analyzers, 30 s loop, RSA-signed Kalshi API orders | Kalshi CLAUDE.md |
| `rover_scanner` | rover_scanner | app_net, data_net | — | WebSocket rover — live Kalshi orderbooks, logit pricing | Kalshi CLAUDE.md |
| `ems_executor` | ems | app_net, data_net | — | Execution Management System — broker adapters (Alpaca, Robinhood) | root CLAUDE.md |
| `cemini_os` | cemini_os | edge_net, data_net | 8501 (internal) | Streamlit dashboard | — |
| `deephaven` | deephaven | edge_net, data_net | 10000 (internal) | Real-time data visualization | — |
| `grafana_viz` | grafana | edge_net, data_net | 3000 (internal) | Metrics dashboards, served at /grafana/ | — |
| `cemini_proxy` | nginx | edge_net, app_net | 80:80 | Reverse proxy — routes to dashboard, Grafana | — |
| `cloudflare_tunnel` | cloudflared | edge_net | — | Cloudflare Tunnel for remote access | — |
| `playbook_runner` | playbook | app_net, data_net | — | Observation-only: regime classification, 6 signal detectors, risk engine, 5 min loop | playbook CLAUDE.md |
| `cemini_mcp` | cemini_mcp | app_net, data_net | 127.0.0.1:8002 | FastMCP intelligence server — 10 read-only tools | mcp CLAUDE.md |

**Disabled (profile-gated):** `signal_generator` — superseded by `brain`; use
`docker compose --profile signal_generator up` only for testing.

**Rebuild required after code changes:**
- `brain` — Dockerfile.brain bakes `agents/` — rebuild on any agent change
- `kalshi_autopilot`, `rover_scanner` — Dockerfile.autopilot bakes Kalshi code
- `cemini_mcp` — rebuild after changes to `cemini_mcp/server.py` or `readers.py`
- `coach_analyzer`, `scribe_logger` — live-mounted from repo root; restart only

---

## 3. Intelligence Bus — Redis Channels

### intel:* namespace (IntelPayload envelope)

Every `intel:*` key uses the `IntelPayload` envelope:
`{"value": <mixed>, "source_system": str, "timestamp": float, "confidence": float}`

Publishers use **SET** (for MCP reads via GET) **and** PUBLISH (for subscriber reads).
Both operations are required — MCP tools read via GET, services subscribe via SUBSCRIBE.

| Channel | Publisher | Value type | TTL | Consumers |
|---|---|---|---|---|
| `intel:btc_sentiment` | SatoshiAnalyzer | float −1 to 1 | 10 min | brain, cemini_mcp |
| `intel:btc_spy_corr` | coach_analyzer | float | persistent | cemini_mcp |
| `intel:btc_volume_spike` | SatoshiAnalyzer | BtcVolumeSpikeValue dict | 10 min | brain |
| `intel:conflict_events` | gdelt_harvester | list of event dicts | 1 hr | cemini_mcp |
| `intel:fed_bias` | powell_protocol analyzer | FedBiasValue dict | 1 hr | brain, cemini_mcp |
| `intel:geopolitical_risk` | gdelt_harvester | risk dict (score, level, trend) | 1 hr | cemini_mcp |
| `intel:kalshi_orderbook_summary` | rover_scanner | market summary dict | 10 min | cemini_mcp, kalshi_autopilot |
| `intel:logit_assessments` | rover_scanner | dict of ContractAssessment dicts | 10 min | cemini_mcp |
| `intel:playbook_snapshot` | playbook_runner | PlaybookRegimePayload or signal dict | 10 min | brain, cemini_mcp |
| `intel:portfolio_heat` | coach_analyzer | float 0–1 | 10 min | brain, cemini_mcp |
| `intel:regional_risk` | gdelt_harvester | dict by region | 1 hr | cemini_mcp |
| `intel:social_score` | social_scraper | SocialScoreValue dict | 10 min | brain, kalshi_autopilot |
| `intel:spy_trend` | coach_analyzer | string: bullish/bearish/neutral | 10 min | brain, cemini_mcp |
| `intel:vix_level` | coach_analyzer | float (VIX proxy) | 10 min | brain, cemini_mcp |

### Non-intel channels

| Channel | Direction | Payload | Notes |
|---|---|---|---|
| `trade_signals` | brain → ems_executor | TradeSignalEnvelope JSON | Execution commands |
| `emergency_stop` | broadcast | raw string "CANCEL_ALL" | Kill switch — NOT JSON |
| `strategy_mode` | coach_analyzer → all | raw string | conservative / aggressive / sniper; TTL=persistent |
| `playbook:kill_switch` | playbook KillSwitch → ems | KillSwitchEvent JSON | Triggers CANCEL_ALL flow |

**TTL rule:** Publish frequency must be ≤ TTL/2. analyzer.py publishes every 4 min
with 10 min TTL. A publish-hourly / TTL-5min mismatch caused the historic nil-read bug
(see LESSONS.md). Always verify alignment when setting a new TTL.

---

## 4. Data Contracts — Pydantic Models

All models live in `cemini_contracts/`. Import via `from cemini_contracts.<module> import <Model>`.
Use `safe_validate(Model, data)` at READ boundaries and `safe_dump(instance)` at WRITE
boundaries. Never create local model definitions that duplicate contract models.

### cemini_contracts/intel.py
| Model | Key fields | Used at |
|---|---|---|
| `IntelPayload` | value, source_system, timestamp, confidence | All intel:* READ/WRITE |
| `FedBiasValue` | bias (dovish/hawkish/neutral), confidence | intel:fed_bias value |
| `BtcVolumeSpikeValue` | detected, multiplier, symbol | intel:btc_volume_spike value |
| `PlaybookSnapshotValue` | regime, detail dict | intel:playbook_snapshot value |
| `SocialScoreValue` | score, top_ticker | intel:social_score value |

### cemini_contracts/signals.py
| Model | Key fields | Used at |
|---|---|---|
| `SignalDetection` | symbol, pattern_name, detected, rsi, volume_ratio, confidence | playbook → Redis → MCP |
| `SignalCatalogScan` | symbol, signals list, regime, timestamp | playbook_runner scan output |
| `SignalType` (enum) | EpisodicPivot, MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212 | signal_catalog.py |

### cemini_contracts/regime.py
| Model | Key fields | Used at |
|---|---|---|
| `RegimeSnapshot` | regime, spy_price, ema21, sma50, jnk_tlt_flag, confidence, reason | playbook → intel:playbook_snapshot |
| `PlaybookRegimePayload` | regime, detail dict | intel:playbook_snapshot outer envelope value |
| `RegimeGateDecision` | allowed, regime, confidence, reason, strategy_mode | regime_gate.py output |
| `RegimeClassification` (enum) | GREEN, YELLOW, RED, UNKNOWN | throughout platform |

### cemini_contracts/risk.py
| Model | Key fields | Used at |
|---|---|---|
| `CVaRResult` | cvar_99, var_95, returns_count | risk_engine → playbook_logs |
| `KellyResult` | kelly_fraction, capped_fraction (25% cap), edge, win_rate | risk_engine → playbook_logs |
| `DrawdownSnapshot` | peak_nav, current_nav, drawdown_pct, in_drawdown | risk_engine → playbook_logs |
| `RiskAssessment` | cvar, kelly, drawdown, nav, timestamp | MCP get_risk_metrics() source |

### cemini_contracts/kalshi.py
| Model | Key fields | Used at |
|---|---|---|
| `KalshiOpportunity` | city, bracket, signal, expected_value, edge, reason | WeatherAnalyzer output |
| `AutopilotTradeCandidate` | module, signal, score, odds, city | CeminiAutopilot opportunity list |
| `KalshiPosition` | ticker, position, yes_bid, cost_basis | get_active_positions() output |
| `RoverMarket` | ticker, yes_bid/ask, no_bid/ask, volume, open_interest | rover_scanner market dict |

### cemini_contracts/market.py
| Model | Key fields | Used at |
|---|---|---|
| `MarketTick` | symbol, open, high, low, close, volume, vwap, timestamp | Polygon ingestor → Postgres |
| `MarketEvent` | event_type, symbol, payload, source | event bus boundaries |
| `FearGreedIndex` | value (0–100), classification, timestamp | macro_scraper → analyzer |

### cemini_contracts/playbook.py
| Model | Key fields | Used at |
|---|---|---|
| `PlaybookLog` | log_type, symbol, payload, regime, timestamp | playbook_logger → Postgres |
| `PlaybookSnapshot` | regime, signal, risk, timestamp | playbook_logger publish |
| `PlaybookLogType` (enum) | regime, signal, risk, kill_switch | playbook_logs.log_type column |

### cemini_contracts/trade.py
| Model | Key fields | Used at |
|---|---|---|
| `TradeSignalEnvelope` | pydantic_signal, strategy, price, rsi, reason, source | trade_signals Redis channel |
| `TradeResult` | status, order_id, ticker, action, price, message | EMS adapter return |
| `KillSwitchEvent` | event, reason, timestamp, source | playbook:kill_switch channel |
| `TradeAction` (enum) | buy, sell, hold, short, cover, CANCEL_ALL | signal payloads |
| `StrategyMode` (enum) | conservative, aggressive, sniper, neutral, standard | strategy_mode channel |

### cemini_contracts/discovery.py
| Model | Key fields | Used at |
|---|---|---|
| `DiscoveryOpportunity` | source, ticker, score, reason, timestamp | Step 26 discovery engine |
| `WatchlistEntry` | ticker, source, added_at, metadata | dynamic watchlist |
| `OpportunitySource` (enum) | GDELT, SOCIAL, FUNDAMENTAL, TECHNICAL, WEATHER | DiscoveryOpportunity.source |

### cemini_contracts/pricing.py
Re-exports `ContractAssessment` from `logit_pricing/models.py` — see Section 7.

### Utilities (cemini_contracts/_compat.py)
- `safe_validate(ModelClass, data)` — validates dict → model, returns None on error
- `safe_dump(instance)` — serializes model → JSON string, handles Decimal/datetime

---

## 5. MCP Intelligence Tools

Server: `http://localhost:8002` (localhost only, Streamable-HTTP transport).
All tools are annotated `destructive=False, readOnly=True`. Safe to call concurrently.
Stale data is always flagged: `stale=True` + `age_seconds` in every response.

| # | Tool | Returns | Use when |
|---|---|---|---|
| 1 | `get_regime_status()` | regime (GREEN/YELLOW/RED), spy_price, ema21, sma50, confidence, reason, stale | Before any buy-side modification — verify gate is not RED |
| 2 | `get_signal_detections(ticker?)` | Latest signal from 6-pattern catalog; filter by ticker | Checking what pattern fired most recently |
| 3 | `get_risk_metrics()` | CVaR 99th, Kelly fraction, NAV, drawdown state — sourced from Postgres, not Redis | Verifying risk headroom before sizing changes |
| 4 | `get_playbook_snapshot()` | Raw IntelPayload envelope from intel:playbook_snapshot | Debugging snapshot content; prefer #1 or #2 for structured data |
| 5 | `get_kalshi_intel(category?)` | Active market counts, category breakdown, orderbook tickers | Checking Kalshi market availability by category |
| 6 | `get_geopolitical_risk()` | Score 0–100, level, trend, top event, regional breakdown, top 5 conflict events | Checking if macro risk should suppress Kalshi orders |
| 7 | `get_sentiment(source?)` | btc_sentiment, fed_bias, spy_trend, vix_level, portfolio_heat, btc_spy_corr | Cross-asset sentiment snapshot; pass source= for a single field |
| 8 | `get_strategy_mode()` | mode (conservative/aggressive/sniper) + supporting signals + staleness | Understanding why a trade was sized a certain way |
| 9 | `get_data_health()` | ok/stale/missing status per intel:* key + Postgres connectivity | First call to verify system is alive; diagnose which pipeline is down |
| 10 | `get_contract_pricing(ticker?)` | ContractAssessment per Kalshi ticker: mispricing score, regime (diffusion/jump), human_review flag | Checking logit-space edge before manual Kalshi intervention |

**Workflow:** Call `get_data_health()` first. If stale keys are present, identify the
responsible publisher from Section 3 and check that container's logs.

---

## 6. Logit-Space Contract Pricing

Library at `logit_pricing/`. Imported by `kalshi_autopilot`, `rover_scanner`, and `cemini_mcp`.

### Core transforms (logit_pricing/transforms.py)
- `logit(p)` — maps probability p ∈ (0,1) to ℝ; clamp-safe (P_MIN=0.001, P_MAX=0.999)
- `inv_logit(x)` — inverse logit back to probability
- `logit_array(arr)` — vectorized; **returns tuple `(logits, invalid_mask)` — always unpack**

### Indicators (logit_pricing/indicators.py)
- `logit_ema(prices, alpha)` — logit-space EMA
- `logit_rsi(prices, period)` — Wilder SMMA-based RSI (NOT SMA — see Rule 5)
- `logit_bollinger(prices, period, n_std)` — logit-space Bollinger bands
- `mean_reversion_score(price, mu, sigma)` — normalized mean-reversion signal

### Jump-diffusion (logit_pricing/jump_diffusion.py)
- `detect_jump(logit_delta)` — flags delta > JUMP_MIN_ABS_LOGIT (0.20) as jump event
- `classify_regime(history)` — diffusion vs. jump regime classification
- `fair_value_probability(logit_history)` — time-decayed fair value estimate

### Precision rules (logit_pricing/precision.py)
- Use `Decimal` for intermediates whenever p is near 0 or 1
- `multiply_before_divide()` — always multiply numerator components before dividing
- `assert_finite(value)` — call after every pricing output; NaN/Inf must never escape
- `clamp_probability(p)` — enforces P_MIN=0.001, P_MAX=0.999

### Pricing engine (logit_pricing/pricing_engine.py)
`LogitPricingEngine.assess_contract(ticker, orderbook_history)` → `ContractAssessment`

### ContractAssessment (cemini_contracts/pricing.py → logit_pricing/models.py)
Fields: ticker, yes_bid, fair_value_prob, mispricing_score, regime (diffusion/jump),
confidence, human_review (True if jump regime), timestamp.

### Integration points
| Service | Integration | Notes |
|---|---|---|
| SatoshiAnalyzer | 70/30 blend: `0.7 × existing_score + 0.3 × logit_mispricing` | logit enriches BTC Kalshi contracts |
| rover_scanner | Per-market assessment published to `intel:logit_assessments` | Requires 10+ orderbook observations per ticker |
| Exit engine | `logit_exit_signal()` fires before 90¢ TP / 10¢ SL backstops | Sensitivity via `LOGIT_EXIT_SENSITIVITY` env var (default 1.0) |
| cemini_mcp | `get_contract_pricing()` reads `intel:logit_assessments` | Exposes assessments to external AI agents |

---

## 7. Decision Architecture

### QuantOS path (equities + crypto)
```
Polygon tick ingestion (polygon_ingestor)
  → raw_market_ticks table (Postgres)
    → QuantBrain.analyze() — RSI-14 via numpy, rolling 1000-price window
      → confidence score + macro FGI overlay
        → Regime gate check (trading_playbook/regime_gate.py)
          → MoneyManager sizing (fractional Kelly)
            → ExecutionEngine → BrokerAdapter (Alpaca primary, Robinhood fallback)
              → Postgres trade_history + JSONL archive
```

### Kalshi path (prediction markets)
```
CeminiAutopilot.scan_and_execute() — 30 s loop (kalshi_autopilot)
  ├─ SatoshiAnalyzer   → btc_score  (BTC multi-TF TA + 70/30 logit blend)
  ├─ PowellAnalyzer    → yield_curve (MOCK DATA — not live)
  ├─ SocialAnalyzer    → social_score [gated: SOCIAL_ALPHA_LIVE=true required]
  ├─ WeatherAnalyzer   → best_opp    [gated: WEATHER_ALPHA_LIVE=true required]
  └─ MuskPredictor     → musk_status (tweet velocity)
    → Score ranking → logit mispricing overlay
      → Guards: held? blacklisted? score >= threshold?
        → Kelly allocation → RSA-PSS signed Kalshi API order
          → Postgres kalshi_trades + JSONL archive
```

### Playbook path (observation only — no orders)
```
trading_playbook/runner.py — 5 min scan loop
  ├─ MacroRegime.classify() → GREEN/YELLOW/RED (SPY vs EMA21/SMA50 + JNK/TLT)
  ├─ SignalCatalog.scan_symbol() → 6 detectors
  │    EpisodicPivot | MomentumBurst | ElephantBar | VCP | HighTightFlag | InsideBar212
  └─ RiskEngine.assess() → CVaR 99th, Kelly fraction, DrawdownMonitor
    → PlaybookLogger.log_*()
      → Postgres playbook_logs (JSONB payload)
      → JSONL /mnt/archive/playbook/
      → intel:playbook_snapshot (Redis)  ← MCP tools read from here
```

**Regime gate thresholds:**
| Regime | BUY threshold | SELL/SHORT |
|---|---|---|
| GREEN | 0.55 | 0.55 |
| YELLOW | 0.71 | 0.50 |
| RED | 0.74 | 0.45 |
Catalyst bonus: +0.10 for EpisodicPivot or InsideBar212 in YELLOW/RED only.

---

## 8. Critical Rules

Rules 1–15 are hard constraints. Do NOT bypass without explicit user approval.

**R1. Quarantine.** Never read or reference data from `/opt/cemini/archives/data_quarantine/`.
It is pre-regime-gate data, methodologically contaminated for RL training.

**R2. Harvesters.** Never stop, restart, or redeploy `playbook_runner`, `gdelt_harvester`,
`social_scraper`, or `macro_scraper` without explicit approval. They accumulate RL training
data 24/7. Loss is unrecoverable.

**R3. Redis auth.** All Redis connections require `REDIS_AUTH` credential via `REDIS_PASSWORD`
env var. Unauthenticated connections fail silently — no error, no data.

**R4. Intel bus dual-write.** All `intel:*` publishers must SET (for MCP GET reads) AND
PUBLISH (for subscriber reads). Both operations required; doing only one breaks either
MCP tools or subscriber services.

**R5. RSI algorithm.** `logit_pricing` uses Wilder's SMMA (alpha=1/period). `QuantBrain`
and `trading_playbook` use SMA-based RSI — known inconsistency. Do NOT "fix" the
QuantBrain/playbook RSI without explicit approval; downstream models may depend on it.

**R6. Logit-space math.** Use `Decimal` for intermediate calculations near p=0 or p=1.
Always multiply-before-divide. Always call `assert_finite()` after every pricing output.
Unpack `logit_array()` as a tuple: `logits, invalid_mask = logit_array(arr)`.

**R7. Polygon timestamps.** On the free tier, `ORDER BY timestamp` is wrong — bar close
times lag by hours. Always `ORDER BY created_at` for free-tier Polygon data.

**R8. Postgres connections.** `idle_in_transaction_session_timeout` is 1 minute. Close
cursors promptly. Leaked connections from crashed containers will hold locks.

**R9. strategy_mode semantics.** `strategy_mode` is set by `coach_analyzer` based on
win rate metrics — it is NOT derived from macro regime. This is a known design inconsistency.
Do not "align" them without explicit approval.

**R10. Credentials.** All credentials via `os.getenv()` with safe fallbacks. Never
hardcode. Kalshi RSA signing key is mounted read-only into containers — never bake
it into an image.

**R11. CI requirements.** Before committing: run `flake8` (max-line-length=120; E501
ignored; E999, F821, E741 enforced) and `agnix` (CI pre-check). Rename ambiguous
single-letter variables: `l` → `ln`, `O` → `val`, `I` → `idx`.

**R12. Pydantic contract discipline.** All new data models go in `cemini_contracts/`.
Never create local model definitions in service code that duplicate contract models.
Use `safe_validate()` at READ and `safe_dump()` at WRITE boundaries.

**R13. MCP tool safety.** All new MCP tools must be annotated `destructive=False`. No
write tools exist yet. If adding the first write tool, create a separate server section
and document the change here.

**R14. Test purity.** All tests are pure — no network, no Redis, no Postgres. Mock all
I/O with `unittest.mock`. Run with `python3 -m pytest tests/ -v` from `/opt/cemini/`.
Test count target: 387+ (all green before any commit).

**R15. Token efficiency.** Use RTK to compress verbose CLI output (directory trees,
logs, git diffs, JSON payloads) before sending to context. RTK is installed globally
on this VPS (`rtk <command>`). 60–90% token savings on dev operations.

---

## 9. File System Map

```
/opt/cemini/                            ← Repo root (git) + working directory
├── agents/                             ← LangGraph orchestrator (brain container)
├── cemini_contracts/                   ← Pydantic v2 data contract models (Step 28)
│   ├── intel.py                        ← IntelPayload + intel:* value models
│   ├── signals.py                      ← SignalDetection, SignalCatalogScan
│   ├── regime.py                       ← RegimeSnapshot, RegimeGateDecision
│   ├── risk.py                         ← CVaRResult, KellyResult, RiskAssessment
│   ├── kalshi.py                       ← KalshiOpportunity, RoverMarket
│   ├── market.py                       ← MarketTick, FearGreedIndex
│   ├── playbook.py                     ← PlaybookLog, PlaybookSnapshot
│   ├── trade.py                        ← TradeSignalEnvelope, StrategyMode
│   ├── discovery.py                    ← DiscoveryOpportunity (Step 26)
│   ├── pricing.py                      ← re-exports ContractAssessment
│   └── _compat.py                      ← safe_validate(), safe_dump()
├── cemini_mcp/                         ← MCP Intelligence Server (Step 27)
│   ├── server.py                       ← 10 FastMCP tools (all read-only)
│   ├── readers.py                      ← Redis GET wrappers + Postgres risk reader
│   └── config.py                       ← env var config (REDIS_HOST, MCP_PORT, etc.)
├── core/                               ← Root engine: EMS, brokers, schemas
│   ├── ems/                            ← Execution Management System
│   │   └── adapters/                   ← BrokerAdapter implementations
│   ├── brokers/                        ← Alpaca (primary), Robinhood (fallback)
│   └── schemas/                        ← TradingSignal (used by ems/main.py)
├── logit_pricing/                      ← Logit-space contract pricing (Step 30)
│   ├── transforms.py                   ← logit(), inv_logit(), logit_array()
│   ├── indicators.py                   ← logit EMA, RSI, Bollinger, mean-reversion
│   ├── jump_diffusion.py               ← jump detection, regime classification
│   ├── precision.py                    ← assert_finite, safe_divide, clamp_probability
│   ├── pricing_engine.py               ← LogitPricingEngine.assess_contract()
│   └── models.py                       ← ContractAssessment (Pydantic)
├── Kalshi by Cemini/                   ← Prediction market engine (FastAPI :8000)
│   ├── modules/                        ← Autopilot analyzer modules
│   │   ├── satoshi_vision/             ← BTC multi-TF TA + logit blend
│   │   ├── powell_protocol/            ← Fed rate analysis (uses mock data)
│   │   ├── weather_alpha/              ← Weather contracts [gated: WEATHER_ALPHA_LIVE]
│   │   ├── social_alpha/               ← X sentiment [gated: SOCIAL_ALPHA_LIVE]
│   │   └── musk_monitor/               ← Musk tweet velocity
│   ├── rover_scanner/                  ← WebSocket rover + logit pricing
│   └── CLAUDE.md                       ← Service-level docs
├── QuantOS/                            ← Equity/crypto engine (FastAPI :8001)
│   ├── core/brain.py                   ← QuantBrain: SMA-RSI, rolling 1000-price
│   ├── core/execution.py               ← Buy/sell/bracket + paper mode
│   └── CLAUDE.md                       ← Service-level docs
├── trading_playbook/                   ← Observation-only regime/signal/risk layer
│   ├── macro_regime.py                 ← GREEN/YELLOW/RED classifier
│   ├── signal_catalog.py               ← 6 pattern detectors
│   ├── risk_engine.py                  ← Kelly, CVaR, DrawdownMonitor
│   ├── kill_switch.py                  ← PnL velocity / order rate circuit breaker
│   ├── playbook_logger.py              ← Postgres + JSONL + Redis publisher
│   ├── runner.py                       ← 5-min scan loop entry point
│   └── CLAUDE.md                       ← Service-level docs
├── scrapers/                           ← Data ingestion scripts
│   ├── gdelt_harvester.py              ← GDELT geopolitical risk (Step 14)
│   ├── social_scraper.py               ← X social sentiment
│   └── macro_harvester.py              ← Macro data (FGI, rates)
├── agents/                             ← LangGraph agents (baked into brain image)
│   ├── regime_gate.py                  ← Confidence threshold gate
│   └── coach_analyzer → analyzer.py   ← strategy_mode publisher (root dir)
├── tests/                              ← Shared test suite (387+ tests, all pure)
├── .github/workflows/                  ← CI: lint → pip-audit → bandit → deploy
├── scripts/
│   ├── vet_skill.py                    ← Step 20: SKILL.md security scanner
│   └── generate_docs.py               ← Step 15: auto-documentation generator
├── archives/                           ← JSONL logs per service + data_quarantine/
├── docker-compose.yml                  ← Authoritative service definition
├── CLAUDE.md                           ← Root developer context (all agents read)
├── LESSONS.md                          ← Hard-won debugging insights (append on discovery)
├── SKILL.md                            ← THIS FILE
└── SECURITY.md                         ← Step 20 vetting protocol documentation
```

---

## 10. Known Issues and Debt

Do NOT fix these unprompted. Each item has a reason for staying as-is.

| ID | Location | Issue | Why not fixed yet |
|---|---|---|---|
| C1 | `agents/orchestrator.py` | `publish_signal_to_bus()` is dead code | Safety net — C2 (hardcoded debate logic) must be fixed first |
| C2 | orchestrator | CIO debate logic is hardcoded | Step 7 territory — full LangGraph rework |
| C3 | `core/ems/router.py` | `RiskManager.check_exposure()` computed but never blocks trades | Step 10 risk integration work |
| C4 | all services | Enforced: no hardcoded DB credentials | ✅ Fixed (Step 33) — stay vigilant |
| C5 | `social_alpha/analyzer.py` | `SOCIAL_ALPHA_LIVE=false` default gates signal | Intentional until X data quality confirmed |
| C6 | `kalshi_fix.py` | `get_buying_power()` returns hardcoded $1000 | Needs live Kalshi API buying power query |
| C7 | `weather_alpha/analyzer.py` | `WEATHER_ALPHA_LIVE=false` default gates signal | Intentional until weather data quality confirmed |
| L1 | QuantOS startup | `fresh_start_pending=True` liquidates all positions on restart | By design in paper mode; dangerous in live (Step 10) |
| L2 | QuantOS `history_cache` | In-memory cache lost on container restart | Architectural decision — restarts trigger fresh RSI accumulation |
| L3 | BigQuery legacy | `DataHarvester` writes `market_data`; `CloudSignalEngine` reads `market_ticks` | Legacy code path; do not create new tables to "fix" without migration plan |
| L4 | `powell_protocol` | Uses mock data, not live Fed API | Step TBD — live yield curve integration |
| L5 | `signal_generator` | Disabled (superseded by `brain`) | Profile-gated to prevent duplicate execution |

---

## 11. Extension Patterns

### Adding a new intelligence source

Follow this exact pattern when Step 26 or any new harvester is wired in:

1. Build ingestion service: REST poller or WebSocket subscriber
2. Publish to `intel:<source_name>` via IntelPublisher (SET + PUBLISH both)
3. Define Pydantic model in `cemini_contracts/<module>.py`
4. Add MCP tool to `cemini_mcp/server.py` (annotate `destructive=False`)
5. JSONL archive to `/mnt/archive/<source_name>/`
6. Add Postgres table if historical query needed
7. Pure pytest tests — mock all I/O
8. Docker service: `app_net` + `data_net`; use `Dockerfile.scraper` as base
9. Update Section 3 (Service Topology), Section 4 (Intel Bus), this SKILL.md

### Adding a new broker adapter

1. Implement `BrokerAdapter` interface in `core/ems/adapters/`
2. Add to `core/brokers/factory.py` dispatch table
3. Paper mode by default — live trading requires explicit env var
4. Circuit breaker pattern (see `core/brokers/robinhood.py` for reference)
5. Add health check endpoint consumable by `core/ems/router.py`
6. Note: Alpaca Algo Trader Plus is the designated primary data spine

### Adding a new signal detector

1. Add detector class to `trading_playbook/signal_catalog.py`
2. Detector returns a `SignalDetection` model (cemini_contracts/signals.py)
3. Register in `trading_playbook/runner.py` scan loop
4. Signal fires → logged via `PlaybookLogger.log_signal()` → `intel:playbook_snapshot`
5. Visible via `get_signal_detections()` MCP tool immediately
6. Add to `SignalType` enum in `cemini_contracts/signals.py`

### Adding a new MCP tool

1. Add `@mcp.tool(annotations={"destructive": False, "readOnly": True})` function to `cemini_mcp/server.py`
2. Use `readers.read_intel(key)` for intel:* keys, `readers.read_raw(key)` for raw strings
3. Always return `stale` and `age_seconds` fields
4. Rebuild and restart `cemini_mcp` container
5. Update Section 5 (MCP Tools) in this SKILL.md

---

## 12. Operational Quick Reference

### Verify system health
```bash
# Check all intel pipeline freshness (start here)
# Use MCP tool: get_data_health()

# Check running containers
docker compose ps

# Check specific service logs
docker compose logs --tail=50 <service_name>
```

### Run tests
```bash
cd /opt/cemini
PYTHONPATH=/opt/cemini python3 -m pytest tests/ -v          # full suite
PYTHONPATH=/opt/cemini python3 -m pytest cemini_mcp/tests/  # MCP only
PYTHONPATH=/opt/cemini python3 -m pytest logit_pricing/tests/ # logit only
```

### Rebuild and redeploy a service
```bash
cd /opt/cemini
docker compose build <service_key>
docker compose up -d <service_key>
```

### Live-mounted services (restart only, no rebuild)
- `coach_analyzer` (container: analyzer)
- `scribe_logger` (container: logger)
- `playbook_runner` (container: playbook)

### CI pipeline (GitHub Actions)
lint (flake8) → pip-audit → bandit → [TruffleHog + SSH deploy] ∥ [update-docs]
All jobs must be green. bandit uses `-ll -ii`. Hosts bound to `0.0.0.0` need `# nosec B104`.

### Environment files
- Root services: environment configuration file at `/opt/cemini/` root (not committed to git)
- Kalshi services: `/opt/cemini/Kalshi by Cemini/` — separate environment configuration file
- Kalshi RSA signing key: mounted read-only into `kalshi_autopilot` and `rover_scanner`

---

*SKILL.md last updated: Step 30 (Logit Pricing) complete. 20 active services. 387 tests.*
*Update this file when completing Steps 26, 31, or any step that adds services or channels.*
