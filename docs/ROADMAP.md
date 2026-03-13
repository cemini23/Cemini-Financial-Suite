# Cemini Financial Suite — Active Checklist & Development Roadmap

**Last updated:** Feb 26, 2026
**Author:** Project owner + Claude analysis sessions
**Purpose:** Living document for solo founder. Each development step contains enough context for a fresh Claude CLI session to understand the full system and produce working code.

---

## PART 1: DO NOW (While the System Harvests Clean Data)

These are non-coding tasks you should handle personally while the playbook runner, harvesters, and regime gate accumulate clean training data over the next 2-4 weeks.

### Business Formation & Legal

- [ ] **Consult a tax professional about LLC formation + Section 475(f) MTM election**
  - You need a Florida single-member LLC for the operating entity (OpCo)
  - The 475(f) Mark-to-Market election eliminates wash sale rules for your algo trading — critical for high-frequency strategies
  - This election has a HARD DEADLINE: must be filed by the unextended due date of the tax return for the year PRIOR to when you want it effective
  - Ask about: pass-through taxation, estimated quarterly payments, Section 174 R&E expensing for dev costs
  - Florida has no state personal income tax — the LLC avoids the 5.5% state corporate tax that a C-Corp would pay

- [ ] **Research Wyoming LLC for IP HoldCo**
  - Separate entity to hold ownership of your algorithms, model weights, training data, and source code
  - Licenses the IP to your Florida OpCo via a formal intercompany agreement
  - If OpCo ever gets sued, the IP is insulated in a separate legal entity
  - Wyoming offers strong privacy, no state income tax, low fees

- [ ] **Broward County Business Tax Receipt (BTR)**
  - Required even for home office operations in Davie, FL
  - Apply for a Home Occupation BTR through the Town of Davie
  - Cheap but legally necessary — avoids delinquency penalties
  - URL: https://www.davie-fl.gov/194/Business-Tax-Receipt

- [ ] **Research Interactive Brokers corporate account requirements**
  - When ready for live trading, IBKR is the institutional-grade target brokerage
  - Corporate LLC account requires: Legal Entity Identifier (LEI), $500 minimum equity, EIN
  - Professional Subscriber market data fees are higher for corporate entities — budget for this
  - TWS API (Python) for algo execution, REST API for account management
  - FIX CTCI for lowest latency (min $1,500/month commission) — future consideration only

### Security (IMMEDIATE)

- [ ] **Rotate Robinhood credentials**
  - RH_USERNAME and RH_PASSWORD are stored in plaintext in /opt/cemini/.env and /opt/cemini/QuantOS/.env
  - Change your Robinhood password, ensure 2FA is enabled
  - Verify .env is in .gitignore: `grep '.env' /opt/cemini/.gitignore`
  - Verify .env was never committed: `git log --all --full-history -- '*.env' | head -20`
  - Long-term: migrate all credentials to Docker secrets or HashiCorp Vault

### Daily Monitoring (5 min/day)

- [ ] **SSH in once daily and run a quick health check:**
  ```
  ssh user@5.161.53.103
  docker ps --format "table {{.Names}}\t{{.Status}}" | head -20
  ```
  - All 18 containers should show "Up"
  - Watch for any restart counts climbing (indicates crash loops)

- [ ] **Check playbook regime classification matches reality:**
  - Is the market actually risk-on or risk-off?
  - Does the regime (GREEN/YELLOW/RED) match your gut reading of SPY + VIX + news?
  - If it consistently disagrees with your judgment, note why — this calibrates your trust in the system

- [ ] **Watch for the first regime gate block:**
  - `docker logs brain --since '24 hours ago' | grep "BLOCKED_BY_REGIME"`
  - The first time you see this message, the gate is proven working in production
  - If you NEVER see it after a week, the brain may not be generating BUY signals at all (which could be its own issue)

### Knowledge Building

- [ ] **Read through the Insights from Gemini doc entries #001-#023**
  - These map to the six tactical setups in your signal_catalog.py
  - Understanding the nuance helps you evaluate whether detected signals make sense
  - Pay special attention to: Episodic Pivot (gap >4% on highest volume) and VCP (volatility contraction pattern) — these are your highest-probability setups

- [ ] **Track market events manually for 2 weeks**
  - Keep a simple log: date, SPY close, regime the system assigned, any signals detected, what you would have done
  - This becomes your ground truth for evaluating the playbook's accuracy before trusting it with real capital

---

## PART 2: DEVELOPMENT ROADMAP (Steps 1-13)

Each step below contains enough context for a fresh Claude CLI session to understand the full system and produce working code. Paste the relevant step as your prompt.

---

### STEP 1: Harden CI/CD Pipeline (pip-audit + bandit + Docker caching)

**What exists now:** GitHub Actions workflow at `.github/workflows/` runs flake8 lint (E999/F821 only, E501 ignored) and TruffleHog secret scanning. On push to main, it SSHs to server (5.161.53.103) and deploys via docker-compose.

**What to build:** Add three new jobs to the existing GitHub Actions workflow:

1. **pip-audit** — Scan requirements.txt against the PyPA CVE database. Fail the pipeline if any known vulnerability is found with CVSS score above medium. Use `pip-audit -r requirements.txt --strict`.

2. **bandit** — Static security analysis of all Python source code. Scan for hardcoded credentials, unsafe subprocess calls (shell=True), insecure deserialization. Use `bandit -r . -ll -ii` (low-confidence low-severity minimum). Exclude test files with `--exclude ./tests`.

3. **Docker layer caching** — If the workflow builds Docker images, add `cache-from: type=gha` and `cache-to: type=gha,mode=max` to the docker/build-push-action step. This preserves compiled pip wheels and OS dependencies between builds.

**Constraints:** Do NOT break the existing flake8 + TruffleHog + SSH deploy flow. Add the new jobs as additional steps that run in parallel with lint. The deploy step should depend on ALL security checks passing. Follow existing code standards: flake8 clean (E999/F821), no secrets in code, green CI before moving on.

**Server:** 5.161.53.103, Hetzner VPS, Ubuntu, Docker + docker-compose stack. Repo: https://github.com/cemini23/Cemini-Financial-Suite

---

### STEP 2: Docker Network Segmentation

**What exists now:** All 18 Docker containers run on a flat network where every container can talk to every other container. This means if the public-facing proxy (cemini_proxy) or Cloudflare tunnel is compromised, an attacker has direct access to Postgres, Redis, and all internal services.

**Current containers (docker-compose.yml):**
- **Edge/Public:** cemini_proxy, cloudflare_tunnel, grafana_viz, pgadmin
- **Application:** brain, ems_executor, kalshi_autopilot, coach_analyzer, rover_scanner, playbook_runner, polygon_ingestor, macro_scraper, social_scraper, scribe_logger, cemini_os
- **Data:** postgres, redis, deephaven

**What to build:** Segment the docker-compose.yml into three isolated networks:

1. **edge_net** — Only cemini_proxy, cloudflare_tunnel, grafana_viz, pgadmin, and the cemini_os dashboard. This is the only network exposed to external traffic.

2. **app_net** — All harvester, analyzer, and execution containers. Can reach data_net for DB access. Cannot be reached from edge_net except through cemini_proxy reverse proxy rules.

3. **data_net** — Postgres, Redis, Deephaven only. Only accessible from app_net. Never directly exposed to edge_net.

**Rules:**
- cemini_proxy sits on BOTH edge_net and app_net (it's the bridge)
- grafana_viz and pgadmin sit on edge_net AND data_net (they need DB access for dashboards)
- Application containers sit on app_net AND data_net
- Data containers sit ONLY on data_net

**Constraints:** Zero downtime — do `docker-compose down && docker-compose up -d` as a single operation. Verify all containers come back healthy. Verify harvesters can still write to Postgres/Redis. Verify Grafana can still query Postgres. Verify the Cloudflare tunnel still serves the dashboard. Run the full test suite.

---

### STEP 3: Paper Trade Performance Analysis Dashboard

**What exists now:**
- playbook_logs table in Postgres accumulates regime classifications, signal detections, and risk snapshots every 5 minutes
- JSONL archives at /mnt/archive/playbook/ with the same data
- trade_history and ai_trade_logs are clean (truncated Feb 25, accumulating post-regime-gate data)
- Grafana is running at grafana_viz container
- The playbook runner (trading_playbook/) has: macro_regime.py (GREEN/YELLOW/RED classifier), signal_catalog.py (6 tactical detectors), risk_engine.py (Kelly/CVaR/Drawdown), kill_switch.py

**What to build:** A Grafana dashboard (or Streamlit app) that visualizes:

1. **Regime timeline** — Color-coded bar showing GREEN/YELLOW/RED over time, overlaid with SPY price
2. **Signal detection log** — Table of all signals detected, with symbol, setup type, confidence, suggested entry/stop
3. **Hypothetical P&L** — If the system had taken every signal at the suggested entry with Kelly-sized positions, what would the running P&L be? Track each signal to its outcome (hit target or hit stop)
4. **Risk metrics over time** — CVaR, drawdown, Kelly fraction charts
5. **Kill switch events** — Any near-triggers or actual triggers logged

**Data source:** Query playbook_logs table (has JSONB payload column with all the data). The JSONL files are backup/archive.

**Constraints:** This is READ-ONLY — it does not modify any trading behavior. It's purely for evaluating whether the playbook's signals are profitable before we trust them with real capital or RL training. Use whatever visualization tool is easiest (Grafana panels if SQL is sufficient, Streamlit if you need Python processing).

---

### STEP 4: Kalshi Rewards Scanner

**What exists now:**
- kalshi_autopilot container is running, connected to Kalshi REST API v2
- Kalshi credentials are in environment variables
- The brain generates BUY/SELL signals that the EMS can route to Kalshi

**What to build:** A lightweight scanner that checks for Kalshi promotional offers, reward programs, and fee-free trading events. Kalshi periodically offers new user bonuses, deposit matches, and zero-fee promotional periods.

1. **Scrape/check Kalshi promotions page** — Look for active promos, deposit bonuses, referral rewards
2. **Track reward eligibility** — If there's a "trade X contracts, get Y bonus" promo, track progress
3. **Alert via Redis intel bus** — Publish to intel:kalshi_rewards so the brain knows about free-money opportunities
4. **JSONL logging** — Log all promo findings to /mnt/archive/kalshi_rewards/

**Design pattern (from Polymarket CLI analysis):** Model after Polymarket's rewards command structure — dedicated queries for: active promotions, reward eligibility tracking, fee tier status, maker rebate earnings. Treat reward optimization as a first-class feature, not an afterthought.

**Constraints:** This should be a standalone script that runs on a schedule (daily check is fine). Don't modify the existing kalshi_autopilot. Use the Kalshi API demo environment (demo-api.kalshi.co) for testing if available. Respect rate limits.

---

### STEP 5: X/Twitter Thread Analysis Tool

**What exists now:**
- social_scraper.py collects sentiment from X API (tiers 1/2/3) and stores in sentiment_logs
- The brain reads sentiment scores via SQL query filtering WHERE source LIKE 'x_tier%'
- mock_social is gated behind ENABLE_MOCK_SOCIAL=false

**What to build:** A Streamlit web tool where you can paste a URL to an X/Twitter thread and get:

1. **Thread extraction** — Pull all tweets in the thread, author info, engagement metrics
2. **Sentiment analysis** — Score each tweet and the thread overall (bullish/bearish/neutral)
3. **Entity extraction** — Identify tickers mentioned ($SPY, $AAPL, etc.), key people, catalysts
4. **Signal relevance scoring** — Does this thread contain actionable trading intelligence? Score 0-100.
5. **One-click inject** — Button to push the analysis into sentiment_logs as a high-priority manual signal source

**Design pattern:** Implement dual-format output (`--output table` / `--output json`) on any API endpoints this tool exposes, so scripts and agents can consume results programmatically.

**Constraints:** This is a standalone Streamlit app, NOT part of the main trading loop. It's a manual research tool. Use the X API credentials already in the environment. If the X API free tier doesn't support thread retrieval, use web scraping as fallback. Deploy as a new container in docker-compose.yml on a non-conflicting port (e.g., 8502).

---

### STEP 6: Equity Tick Data — RESOLVED (Polygon Already Handles This)

**Status as of Feb 26, 2026:** COMPLETE — no action needed.

**What exists:** polygon_ingestor.py already handles BOTH crypto (24/7) and equities (market hours only) via Polygon REST API. All 23 equity/ETF symbols are confirmed present in raw_market_ticks: SPY, QQQ, AAPL, MSFT, AMZN, NVDA, META, GOOGL, TSLA, IWM, MARA, COIN, PLTR, SMCI, MSTR, BAC, JPM, GS, NFLX, DIS, AVGO, AMD, UBER.

**How it works:**
- Polygon REST API free tier, 5 calls/min rate limit (13s sleep between batches)
- 60-second polling cycle during market hours
- `_is_market_hours()` gate: Mon-Fri 9:30-16:00 ET only for equities
- Crypto symbols poll 24/7
- Both write to the same raw_market_ticks table

**Known limitation:** No backfill capability. If the system is down during market hours, those ticks are permanently missed. The Feb 25, 2026 gap (system was down from 02:29 UTC through market close) is one lost trading day.

**Future consideration:** If intraday RL training needs higher-frequency data, evaluate upgrading to Polygon Stocks Starter ($29/mo) for real-time WebSocket streaming instead of REST polling. Not needed currently.

---

### STEP 7: Reinforcement Learning Training Loop (Foundation)

**What exists now:**
- Clean post-regime-gate data accumulating in: playbook_logs, trade_history, ai_trade_logs, sentiment_logs, raw_market_ticks, macro_logs
- JSONL archives at /mnt/archive/playbook/
- Trading playbook with regime classifier, 6 signal detectors, risk engine, kill switch
- The "Insights from Gemini" research doc defines the Game of Attrition philosophy: survival > growth, be the House
- The brain currently uses simple RSI/FGI scoring to generate BUY/SELL verdicts (no RL yet)

**What to build:** The foundational RL training infrastructure:

1. **Environment (Gym-compatible):**
   - State space: SPY price/EMA21/SMA50, regime classification, FGI, VIX, JNK/TLT ratio, current positions, unrealized P&L, portfolio heat
   - Action space: BUY (with size), SELL, HOLD for each symbol in watchlist
   - Reward function: Asymmetric — heavily penalize drawdowns and regime violations, moderately reward profitable trades, slightly reward holding cash in YELLOW/RED regimes (Attrition Protocol: survival is rewarded)
   - Episode: One trading day (or one week for swing strategies)

2. **Data pipeline:**
   - Read from Postgres: raw_market_ticks + macro_logs + sentiment_logs + playbook_logs
   - Construct feature vectors matching the state space
   - Split into train/validation/test by date (no look-ahead bias)

3. **Training script:**
   - Use Stable Baselines3 with PPO (Proximal Policy Optimization) as the starting algorithm
   - Log to Weights & Biases (wandb) for experiment tracking: episodic returns, Sharpe ratio, max drawdown, exploration rate
   - Save model checkpoints to /mnt/archive/rl_models/
   - Include the regime gate as a HARD CONSTRAINT in the environment — if regime is RED, the only valid action is SELL or HOLD (the RL agent cannot learn to override the macro classifier)

4. **Paper trade integration:**
   - After training, deploy the model as a new "rl_brain" that reads the same intel bus data
   - Run alongside the existing brain in shadow mode — both generate signals, only existing brain executes
   - Log RL brain decisions to a separate table (rl_shadow_trades) for comparison

**Design pattern:** When the signal pattern library grows beyond 6 detectors, consider YAML-driven strategy definitions (declarative config instead of hardcoded Python classes). See Appendix A for details on this pattern from polymarket-hft.

**Prerequisites:** At least 2-4 weeks of clean post-regime-gate data. Step 3 (performance dashboard) should be done first so you can evaluate signal quality.

**Constraints:** The RL model must NEVER be able to override the kill switch or regime gate. These are hard safety boundaries that exist outside the model's decision space. Use the fractional Kelly sizing from risk_engine.py as position size constraints (25-50% of full Kelly). Train on GPU if available (the Hetzner server may need a GPU upgrade or use cloud GPU for training).

---

### STEP 8: Automated Backtesting in CI/CD

**What exists now:** GitHub Actions runs flake8 + TruffleHog (+ pip-audit/bandit after Step 1). No algorithmic validation.

**What to build:** A CI/CD step that automatically backtests any changes to the trading playbook or RL model before allowing merge to main.

1. **VectorBT integration** — When files in trading_playbook/ or rl_models/ are modified in a PR, automatically run a backtest against the last 60 days of historical data
2. **Minimum Sharpe gate** — If the backtested Sharpe ratio drops below 0.5 (configurable), fail the PR check
3. **Maximum drawdown gate** — If backtested max drawdown exceeds 15%, fail the PR check
4. **Drift detection** — Use EvidentlyAI to compare the current model's inference distribution against the training data distribution. If Jensen-Shannon divergence exceeds 0.2, flag a warning (not a hard fail)

**Data:** Store 60 days of historical OHLCV in Parquet format in an S3 bucket (or local if S3 is not set up). Cache in GitHub Actions using the S3-backed cache strategy if the dataset exceeds 10GB.

**Constraints:** Backtesting must complete in under 5 minutes to keep CI fast. Use VectorBT's vectorized operations (no loop-based backtesting). Only trigger on changes to trading-related files, not documentation or config changes.

---

### STEP 9: Advanced Options Strategies Module

**What exists now:** The system trades equities and crypto spot only. No options capability.

**What to build:** Extend the trading playbook with options-aware strategies:

1. **Covered calls on existing positions** — When regime is GREEN and a held position hits resistance, sell OTM calls to generate income
2. **Cash-secured puts** — When regime is GREEN and a watchlist stock hits support with a bullish signal, sell puts to enter at a discount
3. **Protective puts** — When regime transitions from GREEN to YELLOW, automatically buy puts on largest positions as hedges
4. **Vertical spreads** — Bull call spreads for defined-risk directional bets when signal confidence is high

**Requirements:**
- Options chain data source (IBKR TWS API or Polygon options tier)
- Greeks calculator (delta, gamma, theta, vega) — use QuantLib or py_vollib
- Integration with risk_engine.py — options positions must be included in CVaR and Kelly calculations
- The kill switch must monitor options positions (assignment risk, expiration)

**Broker note:** Robinhood adapter (already integrated, see Appendix B) supports options execution via robin_stocks. Basic options strategies can be tested through RH before IBKR is set up. Complex multi-leg strategies are better suited to IBKR's TWS API.

**Prerequisites:** Step 7 (RL foundation) should be complete. IBKR or RH account ready for options. This is complex and should be approached incrementally — start with covered calls only.

---

### STEP 10: Live Trading Integration (Multi-Broker)

**What exists now:** The EMS executor (ems_executor) handles order routing with a multi-broker architecture. Trade decisions come from the brain via Redis intel bus. Three broker adapters exist:

- **Kalshi** — Connected and active for prediction market contracts
- **Robinhood** — Fully integrated adapter (see Appendix B). Paper mode enabled by default. Supports equities + options via robin_stocks. Circuit breaker trips after 3 consecutive API errors. Credentials in .env (RH_USERNAME, RH_PASSWORD, RH_ACCOUNT_NUMBER).
- **Alpaca** — Broker adapter exists at QuantOS/core/brokers/alpaca.py. Keys present in .env. Pointed at paper-api.alpaca.markets by default. Intended for order execution, not data.

**Multi-broker router:** QuantOS/core/brokers/router.py health-checks all configured brokers. QuantOS/core/brokers/factory.py dispatches by broker name. core/ems/router.py registers adapters in the EMS signal router.

**What to build:** Production-ready live trading through the existing broker infrastructure:

1. **Validate Robinhood adapter end-to-end** — Confirm paper mode works: brain generates signal → EMS routes to RH adapter → robin_stocks submits paper order → fill confirmation logged to trade_history. This pipeline exists but may not have been tested post-regime-gate.

2. **Alpaca paper trading validation** — Same end-to-end test through the Alpaca adapter. Alpaca's paper environment is more robust than RH's unofficial API.

3. **Position synchronization** — Read actual broker portfolio state and reconcile with the system's internal position tracking. Both robin_stocks and alpaca-trade-api support portfolio queries.

4. **Execution confirmation** — Feed fill reports from both brokers back to trade_history for accurate P&L tracking.

5. **Circuit breaker integration** — The kill switch must be able to flatten positions across ALL connected brokers via market orders if triggered. Verify the existing RH circuit breaker (3 consecutive errors) works. Add the same pattern to Alpaca.

6. **Daily P&L limit** — If unrealized + realized P&L drops below -2% of account equity across all brokers, halt all trading for the day.

**Recommended progression:**
1. First: Validate Alpaca paper trading (official API, more reliable)
2. Then: Validate Robinhood paper trading (unofficial API, higher risk of breaking)
3. Then: Small live positions through Alpaca or RH to validate real execution
4. Eventually: IBKR corporate account for institutional-grade execution (requires LLC + LEI)

**Safety requirements:**
- Paper trading mode FIRST on both brokers
- The regime gate must be active and tested before ANY live capital flows
- Maximum position sizes enforced at the EMS level (not just the brain level)
- Kill switch must flatten across all connected brokers simultaneously

**Prerequisites:** Step 7 RL model producing validated signals (or at minimum, the existing brain producing consistent signals), Step 3 dashboard showing signal quality over 2+ weeks. For IBKR: LLC formed, corporate account opened with LEI.

---

### STEP 11: Shadow Testing Infrastructure

**What exists now:** Single production environment. Changes are deployed directly via GitHub Actions SSH.

**What to build:** A Blue-Green or shadow testing architecture:

1. **V-Current / V-Next containers** — When deploying algorithm changes, spin up V-Next containers that receive the same live market data feed
2. **Dual routing** — Market data from Polygon/yfinance is routed to BOTH V-Current and V-Next
3. **V-Next dry run** — V-Next generates trade decisions and logs them to a shadow database WITHOUT executing any orders
4. **Comparison dashboard** — Side-by-side view of V-Current (live) vs V-Next (shadow) decisions, P&L, risk metrics
5. **Promotion workflow** — When V-Next outperforms V-Current over a configurable observation window, promote it to production

**For Kalshi specifically:** Route V-Next shadow trades to Kalshi's demo environment (demo-api.kalshi.co) for realistic order matching simulation.

**Prerequisites:** Step 2 (Docker network segmentation) for proper isolation, Step 3 (dashboard) for comparison visualization.

---

### STEP 12: Copy Trading / Signal Service (Legal Complexity)

**What exists now:** The system generates trading signals for proprietary use only.

**What to build:** IF legally cleared, a mechanism to share signals with external users:

1. **Signal API** — REST endpoint that exposes the regime classification, detected signals, and suggested position sizes (without revealing the underlying algorithm)
2. **Webhook delivery** — Push signals to subscribers via webhook (Discord, Telegram, email)
3. **Performance tracking** — Public track record dashboard showing historical signal accuracy, Sharpe ratio, max drawdown
4. **Subscription management** — Stripe integration for paid signal subscriptions

**Design pattern (from Polymarket CLI analysis):** Use read-only vs authenticated tier model for API access:
- **Public (no auth):** Regime status, signal history, performance metrics, market data
- **Authenticated (API key):** Execute trades, manage positions, access proprietary model outputs
- **Admin (owner only):** Kill switch, strategy configuration, system health

**CRITICAL LEGAL WARNING:** This step triggers SEC/FINRA oversight:
- Providing actionable trading signals to others = investment advice = requires Investment Adviser registration
- If signals auto-execute in user accounts = discretionary portfolio management = requires RIA registration
- The developer of the algo may need to pass the Series 57 exam (FINRA Regulatory Notice 16-21)
- "AI washing" (overstating AI capabilities) is an active SEC enforcement target
- Consider the Florida Fintech Sandbox (Ch. 559.952) as a regulatory pathway

**Prerequisites:** LLC formed, legal counsel consulted on IA/RIA requirements, Step 10 (live trading) proven profitable over 6+ months, Step 11 (shadow testing) to validate signal reliability.

---

### STEP 13: Multi-Exchange Arbitrage Scanner

**What exists now:** Polygon ingestor collects crypto from one source. No cross-exchange price comparison.

**What to build:** A scanner that identifies price discrepancies across exchanges for the same asset:

1. **Multi-feed ingestion** — Connect to 3+ crypto exchanges (Binance, Coinbase, Kraken) via WebSocket for real-time order book data
2. **Spread calculator** — For each asset, calculate the bid-ask spread across exchanges after accounting for fees and transfer times
3. **Opportunity detection** — When spread exceeds a minimum profit threshold (accounting for slippage, network fees, transfer latency), flag the opportunity
4. **Execution readiness** — Route simultaneous buy/sell orders to the relevant exchanges (requires accounts and API keys on each exchange)

**Reality check:** True arbitrage in crypto is extremely competitive. Latency advantages go to co-located HFT firms. This scanner is more useful for identifying persistent mispricing patterns that the RL model can learn from than for direct arbitrage execution.

**Prerequisites:** Step 7 (RL model to learn from arb patterns), accounts on multiple exchanges with API keys.

---

## Quick Reference: Step Dependencies

```
Step 1 (CI/CD Hardening) ──────────────────────────────► Can do NOW
Step 2 (Docker Networks) ──────────────────────────────► Can do NOW
Step 3 (Performance Dashboard) ────────────────────────► Needs 2 weeks of data
Step 4 (Kalshi Rewards) ──────────────────────────────► Can do NOW
Step 5 (X Thread Tool) ───────────────────────────────► Can do NOW
Step 6 (Equity Tick Data) ─────────────────────────────► COMPLETE ✓
Step 7 (RL Training Loop) ─────► Needs Step 3 + 4 weeks of data
Step 8 (Backtesting in CI) ────► Needs Step 1 + Step 7
Step 9 (Options Strategies) ───► Needs Step 7 + RH or IBKR options-enabled
Step 10 (Live Trading) ───────► Needs Step 7 proven + Step 3 validation
Step 11 (Shadow Testing) ─────► Needs Step 2 + Step 3
Step 12 (Copy Trading) ───────► Needs Step 10 + 6 months track record + legal
Step 13 (Arbitrage Scanner) ──► Needs Step 7 + multi-exchange accounts
```

---

## APPENDIX A: Competitive Intelligence — Polymarket CLI Evaluation

**Source:** https://github.com/Polymarket/polymarket-cli (Rust, MIT, v0.1.4, Feb 24 2026)
**Also reviewed:** polymarket-hft (third-party HFT system), polyfill-rs (zero-alloc order book client), polymarket-rs (community SDK)
**Evaluated:** Feb 26, 2026

### What It Is

Official Rust CLI for Polymarket prediction markets. Browse markets, place orders, manage positions, query order books — from terminal or as JSON API for scripts/agents. Clean architecture: `main.rs` (clap CLI parsing) → `commands/` (one module per command group) → `output/` (table + JSON renderers). Early-stage, 23 commits, 3 stars.

### Design Patterns to Adopt

**1. Dual-format output on all commands (`--output table` / `--output json`)**
Every command in their CLI supports both human-readable table output and machine-parseable JSON via a single flag. Errors follow the same pattern — table mode prints to stderr, JSON mode prints structured error to stdout. Non-zero exit code either way.

**Apply to Cemini:** When building the `cemini` CLI tool, Streamlit dashboard (Step 3), X thread tool (Step 5), or signal API (Step 12), enforce dual output from day one. Agents and scripts consume JSON, humans read tables. One codebase, two audiences. Implement as a shared output formatter module that wraps every response.

**2. YAML/JSON-driven strategy definitions (from polymarket-hft, not official CLI)**
The third-party polymarket-hft project defines trading rules declaratively in YAML:
```yaml
policies:
  - id: btc_alert
    conditions:
      field: price
      asset: "BTC"
      operator: crosses_below
      value: 80000
    actions:
      - type: notification
        channel: telegram
        template: "BTC below $80K!"
```
No code changes needed to add/modify strategies. New patterns are added by editing config, not Python files.

**Apply to Cemini:** Currently, adding a new signal detector to signal_catalog.py requires writing a Python class, running tests, pushing through CI, and restarting the playbook_runner container. A YAML-driven pattern catalog would let you define new setups (entry conditions, stop rules, confidence thresholds) in a config file that the runner hot-reloads. Consider this when extending signal_catalog.py beyond the initial 6 detectors. The Python detection logic stays as the engine, but the parameters and pattern definitions become config-driven. This is NOT urgent — the current 6 hardcoded detectors are fine for now — but becomes valuable when the pattern library grows to 15+.

**3. Read-only vs authenticated command tiers**
Polymarket explicitly splits commands into "no wallet needed" (browse, prices, order books, market search) and "wallet required" (trade, cancel, view balances). Most of the CLI works without any authentication.

**Apply to Cemini:** When building the signal API (Step 12), use the same tiered access model:
- **Public (no auth):** Regime status, signal history, performance metrics, market data
- **Authenticated (API key):** Execute trades, manage positions, access proprietary model outputs
- **Admin (owner only):** Kill switch, strategy configuration, system health

**4. Rewards tracking as first-class feature**
Polymarket has dedicated CLI commands: `rewards --date`, `earnings --date`, `current-rewards`, `order-scoring ORDER_ID`, `reward-percentages`. They treat reward/rebate optimization as a core workflow, not an afterthought.

**Apply to Cemini:** Step 4 (Kalshi Rewards Scanner) should follow this pattern. Build dedicated queries for: active promotions, reward eligibility tracking, fee tier status, maker rebate earnings. Kalshi's reward structure incentivizes liquidity provision similar to Polymarket. The scanner should expose these as queryable endpoints, not just background alerts.

**5. `cancel-all` as a first-class command**
`polymarket clob cancel-all` is prominently documented and easily accessible — not buried in emergency procedures. Validates our kill_switch.py approach of broadcasting CANCEL_ALL on Redis. The pattern of making emergency stops trivially accessible is industry standard.

### Architecture Comparison

Their system (polymarket-hft third-party):
```
Clients → Ingestors → Dispatcher → Policy Engine → Action Executor
                                        ↓
                              State Manager + Archiver
```

Our system:
```
Harvesters → Intel Bus (Redis) → Brain/Analyzer → EMS Executor
                                       ↓
                            Postgres + Redis + JSONL Archives
```

Same event-driven pipeline pattern. Their Policy Engine is YAML-configured (declarative), ours is Python-coded (imperative). Their State Manager uses Redis + TimescaleDB, ours uses Redis + PostgreSQL. Architecturally equivalent — confirms our design is aligned with how serious prediction market systems are built.

### What Does NOT Apply

- **On-chain mechanics** (CTF split/merge/redeem, ERC-20 approvals, Polygon gas, wallet management) — Polymarket is blockchain-based. Kalshi is a regulated CFTC exchange with standard REST API. No blockchain infrastructure needed.
- **Rust performance optimizations** (zero-alloc hot paths, sub-millisecond order book processing) — Relevant for HFT, not for our 60-second polling intervals. Python stack is appropriate for current latency requirements.
- **Interactive shell** (`polymarket shell` REPL) — We already have SSH + Claude CLI which is more capable.
- **Proxy wallet / multisig patterns** — Polymarket-specific DeFi infrastructure.

### When to Reference This Section

- **Step 3 (Dashboard):** Use dual-format output pattern for any API endpoints
- **Step 4 (Kalshi Rewards):** Model after Polymarket's rewards/earnings command structure
- **Step 5 (X Thread Tool):** Use dual-format output for Streamlit API responses
- **Step 7 (RL Training):** Consider YAML-driven strategy configs when pattern library grows
- **Step 12 (Signal Service):** Use read-only vs authenticated tier model for API access control

---

## APPENDIX B: Robinhood Broker Integration (Existing)

**Discovered:** Feb 26, 2026
**Status:** Fully integrated, paper mode enabled by default

### What Exists

Robinhood is already a complete broker adapter in the multi-broker execution router. It is NOT a data source — Polygon handles all market data ingestion. RH is purely for order execution.

**Core components:**
- `core/ems/adapters/robinhood.py` — EMS order execution adapter (implements BaseExecutionAdapter)
- `QuantOS/core/brokers/robinhood.py` — Full broker implementation (implements BrokerInterface)
- `QuantOS/core/brokers/factory.py` — Factory pattern: broker_name == 'robinhood' → RobinhoodAdapter()
- `QuantOS/core/brokers/router.py` — Multi-broker health check and routing (RH alongside Alpaca, others)
- `core/ems/router.py` — EMS signal router registers RobinhoodAdapter
- `ems/main.py` — Instantiates adapter from RH_USERNAME/RH_PASSWORD env vars

**Supporting scripts (11 files):** Login/session management (rh_login.py, manual_login.py, debug_rh.py), account ops (find_accounts.py, sell_all.py, cancel_orders.py), utilities (check_pickles.py, sync.py, verify_connection.py, build_exe.py, wizard.py)

**Auth:** robin_stocks library (>=3.0.0 in requirements.txt, >=3.2.1 in QuantOS/requirements.txt), email + password, store_session=True (session token cached to avoid MFA on every restart)
**Safety:** Paper mode enabled by default; circuit breaker trips after 3 consecutive API errors
**Scope:** Market/limit orders for equities and options; fractional share support
**Credentials:** RH_USERNAME, RH_PASSWORD (in both /opt/cemini/.env and QuantOS/.env), RH_ACCOUNT_NUMBER (QuantOS/.env only)

### Other Broker Adapters in the System

- **Alpaca:** QuantOS/core/brokers/alpaca.py — broker adapter for order execution. ALPACA_API_KEY and ALPACA_SECRET_KEY present in .env. Pointed at paper-api.alpaca.markets by default. Official API, more reliable than RH's unofficial robin_stocks.
- **Kalshi:** kalshi_autopilot container — connected to Kalshi REST API v2 for prediction market contracts. Active and functional.
- **IBKR (future):** Not yet integrated. Target for institutional-grade execution after LLC formation.

### Impact on Roadmap

**Step 10 (Live Trading) has three existing broker paths:**
1. **Robinhood (available NOW)** — Already integrated, funded account, supports equities + options. Limitations: unofficial API (robin_stocks reverse-engineers RH endpoints, can break without warning), no official support, TOS gray area for automated trading, limited order types vs IBKR, no FIX protocol.
2. **Alpaca (available NOW)** — Already integrated, official API, paper trading environment more robust. Better for initial automated trading validation.
3. **Interactive Brokers (future)** — Institutional-grade, official API, 100+ order types, FIX CTCI for lowest latency, but requires LLC + LEI + setup time.

**Recommended progression:** Alpaca paper → RH paper → small live positions (Alpaca or RH) → IBKR institutional.

**Step 9 (Options Strategies) is partially unblocked:** Robinhood supports options execution via robin_stocks. Basic options strategies (covered calls, cash-secured puts) could be tested through RH before IBKR is set up. Complex multi-leg strategies are better suited to IBKR's TWS API.

### Security Requirements (CRITICAL)

- [ ] Rotate RH password immediately
- [ ] Verify .env is in .gitignore: `grep '.env' /opt/cemini/.gitignore`
- [ ] Verify .env was never committed: `git log --all --full-history -- '*.env' | head -20`
- [ ] TruffleHog should be catching this in CI — verify it scans for RH credential patterns
- [ ] Long-term: migrate credentials to Docker secrets or HashiCorp Vault

### Data Source Clarification

Robinhood is NOT used for market data ingestion. The data pipeline is:
- **Equities (23 symbols):** Polygon REST API → raw_market_ticks (1-min OHLCV, market hours only)
- **Crypto (7 symbols):** Polygon REST API → raw_market_ticks (1-min OHLCV, 24/7)
- **Macro (FGI + 10Y yield):** macro_scraper → macro_logs (every 5 min)
- **Regime (SPY/JNK/TLT):** yfinance in playbook_runner → playbook_logs (every 5 min)
- **Sentiment:** X API tiers → sentiment_logs (social_scraper)

Do not add Robinhood as a data source. robin_stocks can fetch quotes, but it's rate-limited, unofficial, and redundant with Polygon.

---

## System Architecture Context (For Pasting to New Sessions)

When starting a new Claude session for any of these steps, include this context block:

```
SYSTEM CONTEXT — Cemini Financial Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Server: 5.161.53.103 (Hetzner VPS, Ubuntu 24, Docker + docker-compose)
Repo: https://github.com/cemini23/Cemini-Financial-Suite
Branch: main (auto-deploys via GitHub Actions SSH)

18 Docker containers:
- postgres, redis, deephaven (data layer)
- polygon_ingestor, macro_scraper, social_scraper (harvesters)
- coach_analyzer, brain, ems_executor, kalshi_autopilot (decision/execution)
- playbook_runner, rover_scanner, scribe_logger (analysis/logging)
- cemini_os, cemini_proxy, cloudflare_tunnel, grafana_viz, pgadmin (infra/UI)

Broker Adapters (multi-broker router):
- Kalshi: Active, prediction market contracts via REST API v2
- Robinhood: Integrated, paper mode default, robin_stocks lib, equities + options
- Alpaca: Integrated, paper mode default, official API, equities
- IBKR: Not yet integrated (future, requires LLC)

Trading Playbook (trading_playbook/):
- macro_regime.py: Traffic-light regime (GREEN/YELLOW/RED) based on SPY vs EMA21/SMA50 + JNK/TLT cross-validation
- signal_catalog.py: 6 detectors (EpisodicPivot, MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212)
- risk_engine.py: Fractional Kelly (25% cap), CVaR (99th percentile), DrawdownMonitor
- kill_switch.py: PnL velocity, order rate, latency, price deviation → broadcasts CANCEL_ALL on Redis
- playbook_logger.py: Writes to Postgres (playbook_logs), JSONL (/mnt/archive/playbook/), Redis (intel:playbook_snapshot)
- runner.py: 5-min scan loop

Key integrations:
- Regime gate in agents/orchestrator.py publish_signal_to_bus() blocks BUY signals when regime is YELLOW/RED
- mock_social gated behind ENABLE_MOCK_SOCIAL=false in social_scraper.py
- Intel Bus: Redis pub/sub with keys like intel:playbook_snapshot, intel:spy_trend, intel:strategy_mode
- IntelPublisher/IntelReader pattern for all Redis I/O

Code standards:
- flake8: max-line-length=120, only E999 (syntax) and F821 (undefined names) enforced, E501 ignored
- GitHub Actions: lint → TruffleHog → SSH deploy. Must be green before moving on.
- Tests: pytest, 46+ tests, pure (no network/Redis/Postgres), mocked I/O
- Patterns: os.getenv() for config, logging.getLogger(), psycopg2 direct cursor (no ORM), emoji console output

Data pipeline:
- raw_market_ticks: 1-min OHLCV — equities (23 symbols, market hours) + crypto (7 symbols, 24/7) via Polygon REST API
- macro_logs: FGI + 10Y yield every 5 min
- sentiment_logs: X API tiers only (mock_social disabled)
- playbook_logs: regime/signal/risk snapshots every 5 min (JSONB payload)
- trade_history: clean post-regime-gate (truncated Feb 25, 2026)
- ai_trade_logs: clean post-regime-gate (truncated Feb 25, 2026)
- Quarantined pre-gate data: /opt/cemini/archives/data_quarantine/ (CSV backups, do NOT use for training)

WORKFLOW REQUIREMENTS:
- Review relevant files before making changes
- flake8 clean, all tests pass, no secrets exposed
- Commit with clear message, push, verify green GitHub Actions
- Restart only affected containers (not the whole stack)
- Do NOT disrupt running harvesters or playbook_runner
```
