# CEMINI SUITE — PROJECT SUMMARY
*Generated: 2026-02-21 | Last updated: 2026-02-28 | Audited by Claude Sonnet 4.6*
*Intended for: deep analysis and strategic planning*

---

## 1. ARCHITECTURE MAP

### System Overview
Three cooperating systems that share intelligence but execute independently:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CEMINI SUITE                                │
│                                                                 │
│  ┌─────────────┐    Redis pub/sub     ┌──────────────────────┐  │
│  │  agents/    │──"trade_signals"────▶│  ems/main.py         │  │
│  │orchestrator │                      │  (EMS Router)        │  │
│  │ (LangGraph) │                      │  port: internal      │  │
│  └──────┬──────┘                      └──────────┬───────────┘  │
│         │                                        │              │
│  Postgres (TimescaleDB)     Redis 6379           │              │
│  ┌──────────────────────────────────────┐        │              │
│  │  raw_market_ticks                    │        │              │
│  │  trade_history                       │        ▼              │
│  │  ai_trade_logs                       │   Adapters:          │
│  │  sentiment_logs                      │   Coinbase           │
│  │  v_correlation_metrics (view)        │   Robinhood          │
│  └──────────────────────────────────────┘   Kalshi REST        │
│                                             Hard Rock Bet       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  QuantOS  (Stock/Crypto Engine)     Port 8001 FastAPI           │
│                                                                  │
│  TradingEngine ──→ AsyncScanner ──→ brain.QuantBrain (RSI)      │
│       │                │                                         │
│       │         Alpaca/Yahoo                                     │
│       │                                                          │
│       ├──→ MasterStrategyMatrix                                  │
│       │       ├──→ CloudSignalEngine (BigQuery polls 60s)        │
│       │       └──→ CredibilityEngine/XOracle (tweets+FinBERT)   │
│       │                                                          │
│       ├──→ ExecutionEngine ──→ GlobalRouter ──→ Broker adapters │
│       │       (Alpaca, IBKR, Robinhood, SoFi, Webull, Schwab)   │
│       │                                                          │
│       ├──→ DataHarvester (BigQuery streaming, 2s flush)         │
│       └──→ RiskManager + MoneyManager + TaxEngine + Ledger      │
│                                                                  │
│  interface/server.py  (Jinja2 HTML UI: dashboard, analytics,    │
│                         settings, backtester)                    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Kalshi by Cemini  (Prediction Market Engine)  Port 8000 FastAPI│
│                                                                  │
│  CeminiAutopilot ──→ scan_and_execute() loop (30s)             │
│       ├──→ SatoshiAnalyzer   (BTC multi-timeframe TA)           │
│       ├──→ PowellAnalyzer    (Fed rate + yield curve)           │
│       ├──→ SocialAnalyzer    (X/Twitter + TextBlob)             │
│       ├──→ WeatherAnalyzer   (NWS/OpenWeather forecast arb)     │
│       ├──→ MuskPredictor     (Elon tweet velocity model)        │
│       ├──→ GeoPulseMonitor   (Geopolitical signals)             │
│       └──→ MarketRover       (Kalshi market scanner)            │
│                                                                  │
│  QuantOSBridge ──HTTP──▶ QuantOS :8001/api/sentiment            │
│  CapitalAllocator (Kelly Criterion position sizing)              │
│  execute_kalshi_order() → direct RSA-signed HTTPX calls         │
│                                                                  │
│  frontend/ (vanilla JS SPA + FastAPI backend)                   │
└──────────────────────────────────────────────────────────────────┘
```

### Docker Services (docker-compose.yml)
| Service | Container | Image/Build | Purpose |
|---|---|---|---|
| postgres | postgres | timescale/timescaledb:pg16 | Primary DB (TimescaleDB) |
| redis | redis | redis:7-alpine | Pub/sub message bus |
| pgadmin | pgadmin | dpage/pgadmin4 | DB admin UI |
| polygon_feed | polygon_ingestor | Dockerfile.ingestor | Polygon WebSocket → Postgres |
| brain | brain | Dockerfile.brain | LangGraph orchestrator |
| signal_generator | signal_generator | QuantOS/Dockerfile.brain | QuantOS trading engine |
| logger | scribe_logger | Dockerfile.logger | Trade logging service |
| analyzer | coach_analyzer | Dockerfile.analyzer | analyzer.py (hourly coach) |
| social_scraper | social_scraper | Dockerfile.scraper | Reddit/social feeds |
| macro_scraper | macro_scraper | Dockerfile.scraper | Macro data harvester |
| ems | ems_executor | Dockerfile.ems | EMS signal router |
| cemini_os | cemini_os | ui/Dockerfile.ui | Streamlit dashboard |
| deephaven | deephaven | ghcr.io/deephaven/server | Real-time data viz |
| grafana | grafana_viz | grafana/grafana | Monitoring dashboards |
| nginx | cemini_proxy | nginx:alpine | Reverse proxy (port 80) |
| cloudflared | cloudflare_tunnel | cloudflare/cloudflared | External tunnel |
| playbook | playbook_runner | Dockerfile.playbook | Trading playbook: macro regime + 6 signal detectors + risk engine (observation-only, 5-min loop) |
| rover_scanner | rover_scanner | Dockerfile.autopilot | Kalshi market discovery: paginates all open markets every 15 min, categorizes, publishes intel to Redis |

**Networking:** All services internal except nginx (port 80). No ports exposed directly — nginx routes: `/grafana/*` → Grafana:3000, rest → cemini_os:8501.

### Key Redis Channels
- `trade_signals` — brain → EMS (trade execution commands)
- `emergency_stop` — kill switch
- `strategy_mode` — analyzer sets: "conservative" | "aggressive" | "sniper"
- `intel:btc_spy_corr` — BTC/SPY correlation float
- `macro:fear_greed` — Fear & Greed Index
- `intel:playbook_snapshot` — playbook_runner publishes regime/signal/risk state every 5 min (JSONB)

---

## 2. CURRENT STATE

### Core Infrastructure
| File | Status | Notes |
|---|---|---|
| `docker-compose.yml` | ✅ Functional | Well-structured; minor issues noted below |
| `ingestion/polygon_ingestor.py` | ✅ Functional | WebSocket → Postgres, crypto XT.* stream |
| `analyzer.py` | ✅ Functional | Heatseeker spikes, BTC/SPY correlation, win-rate coach |
| `core/config.py` | ✅ Functional | Credential loader via dotenv |
| `core/schemas/trading_signals.py` | ✅ Functional | Pydantic schema with cross-field validators |
| `core/ems/router.py` | ✅ Functional | EMS signal router |
| `core/ems/base.py` | ✅ Functional | Abstract base adapter |
| `ems/main.py` | ✅ Functional | Redis listener → adapter dispatch |
| `ems/kalshi_rest.py` | ✅ Functional | Kalshi REST v2 client with RSA signing |
| `core/ems/adapters/kalshi_rest.py` | 🔨 Partial | `execute_order` is simulated only — returns stub |
| `core/ems/adapters/kalshi_fix.py` | 🔨 Partial | FIX adapter wired, but qty/price hardcoded (100 @ $0.50) |
| `core/ems/adapters/kalshi_fix_client.py` | 🔨 Partial | FIX session logic present; needs testing |
| `core/ems/adapters/coinbase.py` | 📝 Stub | Class exists; confirm implementation |
| `core/ems/adapters/robinhood.py` | 📝 Stub | Separate from QuantOS version |
| `core/ems/adapters/hardrock.py` | 📝 Stub | Hard Rock Bet adapter; likely placeholder |
| `core/storage/arctic_manager.py` | ✅ Functional | ArcticDB SDK wrapper: write_df, read_to_numpy, get_versions |
| `core/storage/questdb_bridge.py` | ✅ Functional | Queries via Postgres interface on port 8812, aggregates OHLCV via Polars |
| `core/execution/nautilus_engine.py` | 📝 Stub | Nautilus Trader integration stub |
| `agents/orchestrator.py` | 🔨 Partial | LangGraph brain wired; CIO debate uses hardcoded logic (no real LLM call); `publish_signal_to_bus` exits without publishing |
| `agents/prompts.py` | 📝 Stub | Prompt library; likely templates only |
| `agents/format_guardrail.py` | 📝 Stub | Uses `pydantic_ai.Agent` with `openai:gpt-4o` — inconsistent with the rest of the suite which uses GCP/Gemini |
| `export_grafana.py` | ✅ Functional | One-shot Grafana export utility |
| `logger_service.py` | ✅ Functional | Listens on Redis `trade_signals`, inserts to Postgres `trade_history`; creates table on first run |
| `panic_button.py` | ✅ Functional | Publishes CANCEL_ALL to Redis `emergency_stop` channel; the kill switch |

### QuantOS System
| File | Status | Notes |
|---|---|---|
| `QuantOS/core/engine.py` (`TradingEngine`) | ✅ Functional | Full trading loop, bracket orders, sunset report |
| `QuantOS/core/brain.py` (`QuantBrain`) | ✅ Functional | RSI via numpy, rolling 1000-price window |
| `QuantOS/core/execution.py` (`ExecutionEngine`) | ✅ Functional | Buy/sell/bracket + paper mode |
| `QuantOS/core/money_manager.py` | ✅ Functional | Score-based sizing: 90+→5%, 75+→2.5%, else 0% |
| `QuantOS/core/risk_manager.py` | ✅ Functional | Daily 3% stop, 20% position cap, options check |
| `QuantOS/core/harvester.py` | ✅ Functional | BigQuery streaming inserts, batched 500/2s |
| `QuantOS/core/bq_signals.py` | ✅ Functional | BigQuery volume spike + mover queries, 60s poll |
| `QuantOS/core/strategy_matrix.py` | ✅ Functional | Confluence: BQ spike + XOracle sentiment |
| `QuantOS/core/async_scanner.py` | ✅ Functional | Alpaca primary, Yahoo fallback, async burst |
| `QuantOS/core/sentiment/x_oracle.py` | ✅ Functional | Trust scoring + FinBERT integration |
| `QuantOS/core/sentiment/nlp_engine.py` | ✅ Functional | ProsusAI/finbert pipeline, <0.75 conf → neutral |
| `QuantOS/core/brokers/factory.py` | ✅ Functional | 7-broker factory + GlobalRouter |
| `QuantOS/core/brokers/router.py` | ✅ Functional | Time-aware routing: pre-market→Webull, etc. |
| `QuantOS/core/brokers/alpaca.py` | ✅ Functional | Full: market, limit, bracket, quantity orders |
| `QuantOS/core/brokers/robinhood.py` | ✅ Functional | Fractional orders + circuit breaker |
| `QuantOS/core/brokers/ibkr.py` | ✅ Functional | ib_insync + nest_asyncio |
| `QuantOS/core/brokers/kalshi.py` | 🔨 Partial | Auth and positions work; `get_latest_price` and `submit_order` return stubs |
| `QuantOS/core/brokers/schwab.py` | 📝 Stub | Class exists, not verified |
| `QuantOS/core/brokers/sofi.py` | 📝 Stub | Class exists, not verified |
| `QuantOS/core/brokers/webull.py` | 📝 Stub | Class exists, not verified |
| `QuantOS/core/data/streamer.py` | 🔨 Partial | MarketStream for Alpaca/IBKR WebSocket |
| `QuantOS/core/data/bigquery_analyzer.py` | 🔨 Partial | BQ analytics queries |
| `QuantOS/core/tax_engine.py` | ✅ Functional | Wash sale guard + tax estimation |
| `QuantOS/core/ledger.py` | ✅ Functional | Trade record keeping |
| `QuantOS/core/notifier.py` | ✅ Functional | Discord webhook alerts |
| `QuantOS/core/collector.py` | ✅ Functional | DataCollector wrapper |
| `QuantOS/core/options_engine.py` | 🔨 Partial | Options analysis; verify completeness |
| `QuantOS/core/reporting.py` | 🔨 Partial | SunsetReporter email; recipient config needed |
| `QuantOS/interface/server.py` | ✅ Functional | FastAPI: dashboard, analytics, settings, backtester |
| `QuantOS/run_app.py` | ✅ Functional | Entry point launching engine + UI |

### Kalshi by Cemini System
| File | Status | Notes |
|---|---|---|
| `modules/execution/autopilot.py` (`CeminiAutopilot`) | ✅ Functional | Live trading loop, RSA signing, exit engine |
| `modules/satoshi_vision/analyzer.py` | ✅ Functional | Multi-timeframe BTC TA (SCALP/SWING/MACRO) |
| `modules/satoshi_vision/charts.py` | ✅ Functional | CCXT candle fetcher |
| `modules/satoshi_vision/technicals.py` | ✅ Functional | pandas-ta indicators (RSI, MACD, BB, VWAP, ATR) |
| `modules/powell_protocol/analyzer.py` | ✅ Functional | Treasury yields + QuantOS bridge + Kalshi arb |
| `modules/weather_alpha/analyzer.py` | 🔨 Partial | Simulated Kalshi order book prices (not live) |
| `modules/weather_alpha/sources.py` | ✅ Functional | NWS + OpenWeather multi-source consensus |
| `modules/musk_monitor/predictor.py` | ✅ Functional | Tweet velocity + empire/launch data model |
| `modules/musk_monitor/x_api.py` | 🔨 Partial | X API polling; fallback to proxy if token missing |
| `modules/musk_monitor/sources.py` | 🔨 Partial | Empire/SpaceX data; some mock data |
| `modules/musk_monitor/personality.py` | 🔨 Partial | Bio/meme factors; hand-coded heuristics |
| `modules/musk_monitor/scheduler.py` | 📝 Stub | Scheduling wrapper |
| `modules/social_alpha/analyzer.py` | 🔨 Partial | CRITICAL: Uses simulated tweet data, not live X API |
| `modules/bridge/quantos_bridge.py` | ✅ Functional | HTTP bridge to QuantOS :8001 |
| `modules/execution/allocator.py` | ✅ Functional | Kelly Criterion position sizing |
| `modules/geo_pulse/monitor.py` | 🔨 Partial | Scans simulated high-tension events (war, carrier deployment, elections); needs live X API |
| `modules/market_rover/rover.py` | 🔨 Partial | Cross-references QuantOS sentiment with Kalshi market names; convergence logic functional |
| `app/main.py` | ✅ Functional | FastAPI app entry point |
| `app/api/routes.py` | ✅ Functional | 12 API endpoints, all modules wired |
| `app/core/config.py` | ✅ Functional | pydantic-settings from .env |
| `app/core/settings_manager.py` | ✅ Functional | Runtime settings R/W |
| `app/core/state.py` | ✅ Functional | GLOBAL_STATE conviction tracker |
| `app/core/database.py` | ✅ Functional | SQLAlchemy async + aiosqlite |
| `app/models/vault.py` | ✅ Functional | BTCHarvest SQLAlchemy model |
| `frontend/index.html` + `app.js` | ✅ Functional | Vanilla JS SPA, polls all endpoints |

---

## 3. DATA FLOW

### QuantOS: Market Data → Decision → Execution
```
Polygon WebSocket (polygon_ingestor.py)
  └─▶ INSERT raw_market_ticks (Postgres/TimescaleDB)

AsyncScanner.scan_market() [every 10s]
  ├─▶ Alpaca SDK batch (200 tickers)
  └─▶ Yahoo async fallback (gaps)
       └─▶ TradingEngine.trade_loop()
             ├─▶ QuantBrain.update_price()  ← rolling numpy array
             ├─▶ DataHarvester.record_tick() ← BigQuery streaming insert
             └─▶ calculate_confidence_score()  [strategies/analysis.py]
                   └─▶ RSI, SMA crossover, volume indicators
                         └─▶ score ≥ threshold?
                               └─▶ ExecutionEngine.execute_buy()
                                     ├─▶ MoneyManager.calculate_position_size()
                                     ├─▶ TaxEngine.is_wash_sale_risk()
                                     └─▶ execute_smart_order() → Broker.submit_order()
                                           └─▶ Ledger.record_trade()
                                                 └─▶ Notifier → Discord

CloudSignalEngine [background thread, 60s]
  └─▶ BigQuery SQL → volume_spikes[], top_movers[]
        └─▶ MasterStrategyMatrix.evaluate_market()
              ├─▶ XOracle.get_active_signals() ← FinBERT-filtered tweets
              └─▶ Confluence: spike + bullish news → execute_dip_buy()
```

### Kalshi by Cemini: Intelligence → Prediction Market Execution
```
CeminiAutopilot.scan_and_execute() [every 30s]
  ├─▶ SatoshiAnalyzer   → BTC multi-TF score
  ├─▶ PowellAnalyzer    → yield curve + QuantOS bridge sentiment
  ├─▶ SocialAnalyzer    → X trader sentiment (TextBlob polarity)
  ├─▶ WeatherAnalyzer   → NWS/OWM forecast consensus
  └─▶ MuskPredictor     → tweet velocity + empire data
        └─▶ Opportunities ranked by score
              └─▶ best_trade passes guards:
                    ├─▶ Not already held
                    ├─▶ Not in blacklist (4h post-exit cooldown)
                    └─▶ Score ≥ global_min_score
                          └─▶ CapitalAllocator.calculate_position_size() [Kelly]
                                └─▶ execute_kalshi_order() → RSA-signed HTTPX POST
                                      └─▶ Kalshi API /portfolio/orders

Exit Engine [every 30s]:
  yes_bid ≥ 90¢ → sell (Take Profit)
  yes_bid ≤ 10¢ → sell (Stop Loss)
```

### Trading Playbook: Regime → Signals → Risk → Logging
```
playbook_runner (every 5 min, observation-only):
  ├─▶ macro_regime.py → yfinance SPY/EMA21/SMA50 + JNK/TLT → GREEN|YELLOW|RED
  ├─▶ signal_catalog.py → 6 detectors query raw_market_ticks
  ├─▶ risk_engine.py → Fractional Kelly / CVaR / Drawdown
  ├─▶ kill_switch.py → PnL velocity / order rate / latency checks
  └─▶ playbook_logger.py
        ├─▶ INSERT playbook_logs (Postgres JSONB)
        ├─▶ JSONL append /mnt/archive/playbook/
        └─▶ SET intel:playbook_snapshot (Redis)

Regime Gate (agents/orchestrator.py):
  BUY signal → regime GREEN? → pass to EMS
                regime YELLOW|RED? → "⛔ Trade blocked" (logged, not executed)
```

### agents/orchestrator.py: LangGraph Brain (currently unused in main flow)
```
TradingState → technical_analyst_node (stub)
             → fundamental_analyst_node (stub)
             → sentiment_analyst_node (stub)
             → cio_debate_node [HARDCODED: confidence=0.85, always BUY]
             → publish_signal_to_bus [INCOMPLETE: returns NO_ACTION_TAKEN]
```

---

## 4. CREDENTIAL HANDLING

### Loading Mechanism
- **Root-level `.env`**: loaded via `python-dotenv` in `core/config.py`, `docker-compose.yml` via `env_file`
- **Kalshi by Cemini `.env`**: loaded by `pydantic-settings` in `app/core/config.py`; also read directly via `dotenv_values()` in `QuantOS/core/brokers/kalshi.py`
- **QuantOS settings**: runtime override via `settings_manager` (JSON file), which takes priority over ENV

### Credentials Map
| Variable | Used By | System |
|---|---|---|
| `POLYGON_API_KEY` | polygon_ingestor, core/config | Root |
| `ALPACA_API_KEY` / `APCA_API_KEY_ID` | AlpacaAdapter, AsyncScanner | QuantOS |
| `ALPACA_SECRET_KEY` / `APCA_API_SECRET_KEY` | AlpacaAdapter, AsyncScanner | QuantOS |
| `RH_USERNAME` / `RH_PASSWORD` | RobinhoodAdapter | QuantOS |
| `KALSHI_API_KEY` | KalshiRESTv2, autopilot, routes | Both |
| `KALSHI_PRIVATE_KEY_PATH` | autopilot, routes | Kalshi |
| `private_key.pem` | Mounted at `/app/private_key.pem` in Docker | Both |
| `GOOGLE_APPLICATION_CREDENTIALS` | DataHarvester, CloudSignalEngine | QuantOS |
| `BQ_PROJECT_ID` / `BQ_DATASET_ID` | BigQuery clients | QuantOS |
| `X_BEARER_TOKEN` | SocialAnalyzer, XMonitor | Both |
| `DISCORD_WEBHOOK_URL` | analyzer.py, ExecutionEngine, notifier | Root/QuantOS |
| `IBKR_HOST` / `IBKR_PORT` | IBKRAdapter | QuantOS |
| `COINBASE_API_KEY/SECRET` | CoinbaseAdapter | EMS |
| `CLOUDFLARE_TUNNEL_TOKEN` | cloudflared service | Infra |
| `REDDIT_CLIENT_ID/SECRET` | social_scraper | Root |

### Security Issues Found
1. **`analyzer.py:49`** — Postgres password `"quest"` hardcoded: `psycopg2.connect(..., password='quest')`. Same in `ems/main.py:26`. **PARTIALLY MITIGATED** (Feb 28). docker-compose.yml now uses env var. analyzer.py patched for idle-in-transaction fix.
2. **`docker-compose.yml`** — `POSTGRES_PASSWORD=quest` and `PGADMIN_DEFAULT_PASSWORD=admin` hardcoded in compose file (not via `.env`). **FIXED.** Now uses `${POSTGRES_PASSWORD:-quest}` and `${PGADMIN_DEFAULT_PASSWORD:-admin}`.
3. **`export_grafana.py:6-7`** — `GRAFANA_USER="admin"`, `GRAFANA_PASS="admin"` hardcoded.
4. **`QuantOS/core/brokers/kalshi.py:24`** — Hardcoded absolute Mac path: `"/Users/<username>/Desktop/Kalshi by Cemini"`. Breaks in Docker or any other machine.
5. **`private_key.pem`** — Present in the repo directory (tracked?). The `.gitignore` should cover it but was not verified in the audit.
6. **`Kalshi by Cemini/.env`** — Separate `.env` from root. Docker compose only mounts root `.env`, so Kalshi secrets may not reach the `ems` container. **FIXED.** docker-compose.yml now explicitly mounts `Kalshi by Cemini/.env` for kalshi_autopilot and rover_scanner.

---

## 5. DEPENDENCIES

### External APIs
| Service | Used By | Auth Method |
|---|---|---|
| Polygon.io WebSocket | polygon_ingestor | API key |
| Alpaca Trading API | AlpacaAdapter, AsyncScanner | Key + Secret |
| Robinhood (robin_stocks) | RobinhoodAdapter | Username + Password session |
| Interactive Brokers (ib_insync) | IBKRAdapter | TWS connection (host:port) |
| Kalshi REST API v2 | autopilot, ems, routes, adapters | RSA private key |
| Google BigQuery | DataHarvester, CloudSignalEngine | GOOGLE_APPLICATION_CREDENTIALS |
| Google Cloud (Vertex, deployment) | CI/CD | Workload Identity Federation |
| X (Twitter) API v2 | SocialAnalyzer, XMonitor, XOracle | Bearer Token |
| OpenWeatherMap | WeatherSource | API key |
| NOAA NWS | WeatherSource | User-Agent header |
| yfinance | PowellAnalyzer, others | No auth (scraping) |
| CCXT | SatoshiAnalyzer (ChartReader) | No auth (public) |
| Discord Webhooks | analyzer, ExecutionEngine, notifier | Webhook URL |
| HuggingFace (ProsusAI/finbert) | FinBERTSentiment | No auth (model download) |
| SoFi, Webull, Schwab | Broker adapters | Varies (stub) |
| Coinbase Advanced Trade | CoinbaseAdapter | API key/secret |
| Hard Rock Bet | HardRockBetAdapter | Bearer token |
| Reddit API | social_scraper | Client ID/Secret |
| Cloudflare Tunnel | infra | Tunnel token |

### Key Python Libraries
**QuantOS:** `alpaca-trade-api`, `ib_insync`, `robin_stocks`, `google-cloud-bigquery`, `transformers` (FinBERT), `torch`, `pandas`, `numpy`, `aiohttp`, `langgraph`, `fastapi`, `pytz`, `nest_asyncio`

**Kalshi by Cemini:** `fastapi`, `httpx`, `tweepy`, `textblob`, `yfinance`, `ccxt`, `pandas-ta`, `cryptography`, `pydantic-settings`, `sqlalchemy`, `aiosqlite`

**Root EMS:** `redis`, `psycopg2`, `pydantic`, `websockets`

---

## 6. CODE QUALITY ISSUES

### Critical (will cause crashes or wrong trades)

**C1 — `agents/orchestrator.py:140`**: `publish_signal_to_bus` returns `{"execution_status": "NO_ACTION_TAKEN"}` without ever publishing to Redis. The LangGraph brain generates verdicts that silently die. No trade ever reaches the EMS through this path.

**C2 — `agents/orchestrator.py:73-86`**: CIO debate node is 100% hardcoded — confidence always 0.85, always BUY. There is no LLM call despite the extensive prompt in the comment. The `pydantic_signal` field in `TradingState` is never populated (missing from the node output), which will cause a KeyError when the schema is eventually used.

**C3 — `QuantOS/core/brokers/kalshi.py:24`**: Hardcoded path `/Users/<username>/Desktop/Kalshi by Cemini` breaks in any Docker container or non-Mac environment. The QuantOS Kalshi adapter cannot work in production as-is.

**C4 — `analyzer.py:49` + `ems/main.py:26`**: Hardcoded DB password `"quest"`. If the Postgres password is ever changed in `.env`, these services will crash without a clear error.

**C5 — `modules/social_alpha/analyzer.py:76-80`**: The `get_target_sentiment()` function that drives the Autopilot's "SOCIAL" signal uses **simulated tweets** hardcoded in the function body, not live X API data. The Autopilot makes real Kalshi trades based on fake sentiment data. This is a logic correctness bug masquerading as a feature.

**C6 — `core/ems/adapters/kalshi_fix.py:23-24`**: `get_buying_power()` always returns `1000.00` hardcoded. Position sizing through this adapter is based on a fictional balance.

**C7 — `modules/weather_alpha/analyzer.py:18-20`**: The Kalshi order book prices used for arbitrage calculations are simulated (`"price": 0.15, 0.45, 0.10`). The "DIAMOND ALPHA" signal is computed against fake market prices. Real Kalshi market prices are not fetched.

### Logic (suboptimal decision-making, missing edge cases)

**L1 — `QuantOS/core/engine.py:185-188`**: `fresh_start_pending = True` on every startup causes liquidation of all positions on each bot restart. In production, a restart during a volatile moment will force-sell everything at market.

**L2 — `QuantOS/core/money_manager.py`**: Position sizing uses `buying_power` (cash) as the base, not portfolio equity. In a margin account or after gains, this significantly under-sizes positions. Also: no correlation check — the bot can hold 20 positions in the same sector simultaneously.

**L3 — `QuantOS/core/risk_manager.py:28-29`**: `check_exposure()` takes a `portfolio` object but the code path from `ExecutionEngine` never calls it — only `get_exit_levels()` is used. The daily 3% stop and 20% position cap are computed but never block execution.

**L4 — `analyzer.py:97-101`**: Win rate is calculated only on SELL trades where `reason != 'SL'` (stop-loss). Trades that are still open or were stopped out differently are excluded, inflating the apparent win rate used to set `strategy_mode`.

**L5 — `modules/execution/autopilot.py:282-296`**: The blacklist check only blacklists tickers by city name substring match, which is error-prone. A ticker named "MIA" and a city "MIA" will collide unexpectedly.

**L6 — `modules/powell_protocol/analyzer.py:69`**: Kalshi market probabilities are hardcoded mock values: `{"PAUSE": 0.60, "HIKE_25": 0.05, "CUT_25": 0.35}`. No live Kalshi market data is fetched for this module. The "MACRO ALPHA" signal is based on fake market prices. Same issue in `geo_pulse/monitor.py` (simulated war/election events).

**L7 — `QuantOS/core/strategy_matrix.py:54-58`**: Scenario B ("Confirmed Breakout") routes to `execute_dip_buy()`, which is the same logic as Scenario A (dip buying). A breakout on bullish news is a momentum trade — entry logic should differ (no contrarian dip buy needed).

**L8 — RSI calculation in `QuantBrain`**: Uses simple average (SMA-RSI), not Wilder's Smoothed Moving Average (SMMA-RSI). All RSI readings are approximate and will diverge from standard indicators, especially on shorter time windows.

### Architecture (tight coupling, redundancy, scalability)

**A1 — Dual EMS systems**: There are two parallel execution paths for Kalshi:
  - `agents/orchestrator.py` → Redis `trade_signals` → `ems/main.py` → `core/ems/adapters/kalshi_rest.py` (simulated only)
  - `modules/execution/autopilot.py` → direct HTTPX RSA call (live, working)

  Only the second path works for live trading. The Redis/EMS path is wired but the adapter stub never executes real orders.

**A2 — QuantOSBridge assumes local localhost**: `QuantOSBridge(host="127.0.0.1", port=8001)` — in Docker, the QuantOS service is `signal_generator`, not localhost. The bridge will always fail in containerized deployment, silently returning mock sentiment.

**A3 — No shared context between QuantOS and Kalshi**: Powell Protocol's Kalshi signals could trigger QuantOS hedges, and QuantOS volatility spikes could boost Kalshi weather/social confidence. The bridge endpoint exists (`/api/hedge`) but the triggering logic from QuantOS side is absent.

**A4 — BigQuery table name inconsistency**: `DataHarvester` writes to `BQ_TABLE_ID` defaulting to `"market_data"`. `CloudSignalEngine` queries `BQ_TABLE_ID` defaulting to `"market_ticks"`. Unless both env vars are explicitly set to the same table, no data harvested by QuantOS will be queryable by the signal engine.

**A5 — `signal_generator` Docker service** builds from `QuantOS/Dockerfile.brain`, but `brain` service builds from root `Dockerfile.brain`. These are likely different entry points doing different things — both depend on postgres and redis but their relationship is unclear.

**A6 — No persistence for QuantOS `executed_trades` / `blacklist`**: Both are in-memory dicts. A restart loses all trade deduplication and cooldown state, potentially doubling positions immediately after restart.

**A7 — FinBERT loads on every `QuantBrain` initialization**: The model download (~400MB) happens synchronously at startup with no caching check. First boot will be very slow; Docker container will time out if health checks are configured.

### Style (flake8, naming, documentation)

**S1** — `analyzer.py` has all logic crammed into single lines (one-liner chains). Passes flake8 but is unmaintainable.
**S2** — Mixed naming: `ems/kalshi_rest.py` has class `KalshiRESTv2`; `core/ems/adapters/kalshi_rest.py` has `KalshiRESTAdapter`. Confusing.
**S3** — Version strings scattered: `engine.py` says `v13.1.0`, `harvester.py` says `v10.0.0`, routes say `v2.0.10`. No single source of truth.
**S4** — No type annotations in `analyzer.py`, `ems/main.py`, `ingestion/polygon_ingestor.py`.
**S5** — `QuantOS/core/brokers/router.py` has `from ib_insync import Stock, MarketOrder, LimitOrder` duplicated inside a method body (already imported at module level).

---

## 7. IMPROVEMENT OPPORTUNITIES

### Cross-Brain Intelligence Sharing
The QuantOSBridge exists but only provides a one-way pull (Kalshi asks QuantOS for sentiment). What's needed:
- **QuantOS → Kalshi push**: When QuantOS detects a BTC volume spike or S&P flash crash, it should publish to Redis `intel:*` channels that the Autopilot reads in real time.
- **Kalshi → QuantOS hedge trigger**: When Powell Protocol identifies a rate decision probability edge (e.g., CUT_25 underpriced), Kalshi should POST to QuantOS `/api/hedge` with a hedging recommendation (e.g., buy TLT puts as insurance).
- **Shared signal bus schema**: Both systems should write to a common Redis `intel:` namespace: `intel:btc_sentiment`, `intel:fed_bias`, `intel:social_score`, `intel:weather_edge`. Each system reads the keys it cares about.
- **Market-specific parameters**: Kalshi requires conviction scores >70 (binary, expiry-bounded); QuantOS needs RSI+volume confluence. The `TradingSignal` Pydantic schema handles routing correctly but needs to flow end-to-end.

### Polymarket/Kalshi Account Analyzer
To build a "analyze other users' strategies" tool:
- **Kalshi API**: The public `/markets` endpoint returns all active markets with `yes_bid/ask`. Historical settlement data is available. No endpoint for individual account history exists publicly.
- **What's buildable**: Scrape public leaderboard/activity feeds if available; analyze market pricing inefficiencies across all open markets; compare your own portfolio to market consensus to identify contrarian edge.
- **Missing**: No Kalshi public user API → the tool would need to operate on market pricing patterns, not user-level data. Polymarket has a public GraphQL API with full trade history including wallet addresses — far more analyzable.

### Social Sentiment → Production Grade
The current `SocialAnalyzer` is a prototype. To make it production-grade:
1. Replace simulated tweets with live `tweepy.StreamingClient` (filtered stream, no polling cost).
2. Replace `TextBlob` with the same `FinBERTSentiment` already running in QuantOS — reuse the singleton across both systems.
3. Add X API v2 search for cashtags (`$BTC`, `$SPY`) with volume-weighted aggregation.
4. Track sentiment delta (rate of change), not just current value — a shift from -0.2 to +0.4 is more actionable than a stable +0.3.
5. Add credibility scoring (same as `CredibilityEngine` in QuantOS) to filter noise.
6. Store signals in Redis with TTL so all systems can consume them.

### True Portfolio Management
Currently missing:
- **Portfolio-level position sizing**: MoneyManager uses individual trade sizing but has no concept of total exposure across all open positions. If 10 positions are open, the 11th should be sized smaller.
- **Correlation tracking**: `analyzer.py` computes BTC/SPY correlation but doesn't use it to reduce correlated position sizes. If BTC/SPY correlation > 0.8, a BTC trade adds to existing SPY risk.
- **Rebalancing**: No mechanism to trim winners or add to losers based on portfolio weights.
- **Cross-system P&L**: QuantOS tracks its own ledger; Kalshi by Cemini tracks its own. No unified portfolio view exists.
- **Risk budget**: Daily 3% stop per QuantOS only. Kalshi losses (which can be 100% of a contract) are not factored into the cross-system daily risk budget.

### Scalability Gaps
- BigQuery streaming cost: 500 rows/2s × 60 tickers = ~900K rows/day = ~$0.45/day at current rates. Fine now; grows linearly with tickers.
- Robinhood adapter has 0.5s sleep on every `get_latest_price` call — with 60+ tickers, scanning takes 30+ seconds serially. `AsyncScanner` mitigates this with Alpaca but Robinhood scans are still blocking.
- FinBERT model loaded once at startup — but `CredibilityEngine` is a singleton and `FinBERTSentiment` inside it is initialized once. Not a problem until you need multiple inference workers.
- `TradingEngine.history_cache` holds all historical data in RAM — with 200 tickers × 252 days of OHLCV, this is fine (~50MB). Would need Redis or BigQuery for 1000+ tickers.

---

## 8. ACTIVE DEVELOPMENT ROADMAP

The original priority list has been superseded by a 13-step development roadmap maintained in the project's Research document ("Claude Roadmap" section). As of Feb 28, 2026:

**Completed:** Step 1 (CI/CD Hardening), Step 6 (Equity Tick Data)
**Ready now:** Step 2 (Docker Network Segmentation), Step 4 (Kalshi Rewards Scanner), Step 5 (X Thread Tool)
**Waiting on data:** Steps 3, 7-11, 13

Step 12 (Copy Trading / Signal Service) has been removed — it triggered SEC/FINRA regulatory requirements incompatible with the private-use-first strategy.

---

## APPENDIX A: ADDITIONAL INFRA FINDINGS

### Dockerfile Entrypoints vs docker-compose commands
`Dockerfile.analyzer` and `Dockerfile.logger` both have **placeholder loop** default entrypoints (`time.sleep(60)` forever). This is intentional — docker-compose overrides them via `command:`. Do NOT remove the override lines from compose.

### Redis Password — FIXED
Redis is now password-protected via `--requirepass "${REDIS_PASSWORD:-cemini_redis_2026}"` in docker-compose.yml. All services use the REDIS_PASSWORD environment variable.

### Live Trading is Active
`Kalshi by Cemini/settings.json` has `paper_mode: false, trading_enabled: true`. **Real money is being traded.** Any restart of the Autopilot with `fresh_start_pending = True` (if that logic were ported) would execute live orders immediately.

### X API Budget Tracking
`settings.json` shows `x_api_total_spend: 2.15` against a `x_api_budget_limit: 100.0`. Social scans cost $0.03/scan and budget limiter stops scanning at 90% ($90). This is a reasonable guard but the spend counter resets only if the JSON file is deleted.

### Scrapers Confirmed
`scrapers/` contains `social_scraper.py`, `macro_scraper.py`, `macro_harvester.py`. These are separate from the `Kalshi by Cemini` social engine — they serve the root Postgres/Redis infrastructure.

---

## APPENDIX B: FILES NOT IN GIT / SECURITY NOTES

- `Kalshi by Cemini/private_key.pem` — RSA private key present on disk. Confirm `.gitignore` covers this. **Never commit.**
- `Kalshi by Cemini/data_vault.db` — SQLite DB with trade history present on disk.
- `Kalshi by Cemini/audit_deadcode.log` + `audit_security.log` — Previous audit artifacts.
- `Cemini-Suite/` — Nested git repo / old copy of the project. Should be removed or properly gitignored to prevent confusion.
- `venv_new/` inside `Kalshi by Cemini/` — Committed venv directory with full Python 3.9 installation. **Must be gitignored.** Adds enormous noise to diffs and TruffleHog scans.

---

*End of PROJECT_SUMMARY.md*
