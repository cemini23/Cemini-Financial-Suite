# opportunity_screener — CLAUDE.md

## Service Role

**Step 26.1 — Opportunity Discovery Engine (Phase 1)**

This is the architectural keystone of the Cemini Financial Suite: the **Intelligence-in, ticker-out** layer. Rather than scanning a static watchlist, the engine autonomously discovers market opportunities by extracting tickers from all flowing `intel:*` channels and scoring them with Sequential Bayesian Updating.

The **discovery layer surfaces tickers**; the existing signal machinery (playbook, regime gate, risk engine) evaluates what is surfaced.

## Architecture

```
intel:* channels (Redis GET, polled every 30s)
        │
        ▼
entity_extractor.py  ─── Tier 1 regex (fast)
        │                Tier 2 LLM stub (Phase 3)
        ▼
conviction_scorer.py ─── Sequential Bayesian Updating
        │                Prior × LR → Posterior (odds form)
        ▼
watchlist_manager.py ─── 50-slot dynamic watchlist + 6 core tickers
        │                Promotion (≥0.65) / Demotion (<0.45) / Eviction
        ▼
discovery_logger.py  ─── Postgres hypertable + JSONL (RL training data)
        │
        ▼
intel:discovery_snapshot (every 5 min)
intel:watchlist_update   (every promotion/demotion)
```

## Bayesian Conviction Formula

```
prior_odds       = prior / (1 - prior)
likelihood_ratio = source_weight × extraction_confidence × recency_factor × convergence_bonus
posterior_odds   = prior_odds × likelihood_ratio
conviction       = posterior_odds / (1 + posterior_odds)
conviction       = clamp(conviction, 0.01, 0.99)
```

**Source weights (configurable via SOURCE_WEIGHTS in conviction_scorer.py):**

| Channel | Weight | Rationale |
|---------|--------|-----------|
| `intel:playbook_snapshot` | 1.5 | Internal regime + 6 validated detectors |
| `intel:geo_risk_score` | 1.3 | GDELT — authoritative geopolitical |
| `intel:btc_sentiment`, `intel:fed_bias` | 1.2 | Kalshi modules, calibrated |
| `intel:spy_trend`, `intel:vix_level` | 1.1 | Derived internal signals |
| `intel:weather_edge` | 0.9 | Narrow scope — weather markets |
| `intel:kalshi_oi`, `intel:kalshi_liquidity_spike`, `intel:btc_volume_spike` | 1.0 | Neutral |
| `intel:social_score`, `intel:portfolio_heat` | 0.8–0.9 | Noisy / indirect |
| `intel:kalshi_rewards` | 0.3 | Low signal value for ticker discovery |

**Recency decay:** 1h → ×1.0 | 6h → ×0.8 | 24h → ×0.5 | >24h → ×0.2

**Multi-source convergence bonus:** ×1.3 when 2+ distinct channels mention same ticker within 30-minute window

**Conviction decay:** Every 5 minutes, multiply all non-core conviction scores by 0.995.
A ticker at 0.9 with no new intel decays to ~0.5 in ~12 hours.

## Redis Keys

### Reads
| Key | Description |
|-----|-------------|
| `intel:playbook_snapshot` | Regime + signals |
| `intel:spy_trend`, `intel:vix_level` | Market internals |
| `intel:portfolio_heat` | Exposure metric |
| `intel:btc_volume_spike`, `intel:btc_sentiment` | BTC intelligence |
| `intel:fed_bias` | Fed rate bias |
| `intel:social_score` | Sentiment aggregate |
| `intel:weather_edge` | Weather market intel |
| `intel:geo_risk_score` | GDELT geopolitical risk |
| `intel:kalshi_oi`, `intel:kalshi_liquidity_spike`, `intel:kalshi_rewards` | Kalshi intel |

### Writes
| Key | Description |
|-----|-------------|
| `discovery:convictions` | Hash: ticker → JSON conviction state, TTL 48h |
| `discovery:watchlist` | Sorted set: conviction score → ticker |
| `discovery:watchlist_meta:{ticker}` | Hash: metadata per watchlist member, TTL 96h |
| `intel:watchlist_update` | Latest promotion/demotion event |
| `intel:discovery_snapshot` | Full snapshot every 5 min, TTL 600s |

## Intel Channels Subscribed

All 13 currently flowing `intel:*` channels are polled every 30 seconds:
- `intel:playbook_snapshot`, `intel:spy_trend`, `intel:vix_level`
- `intel:portfolio_heat`, `intel:btc_volume_spike`, `intel:btc_sentiment`
- `intel:fed_bias`, `intel:social_score`, `intel:weather_edge`
- `intel:geo_risk_score`, `intel:kalshi_oi`, `intel:kalshi_liquidity_spike`
- `intel:kalshi_rewards`

**Future channels (design-ready, no wire needed yet):**
`intel:sec_filings`, `intel:congress_trades`, `intel:options_flow`,
`intel:dark_pool`, `intel:unusual_activity`, `intel:shipping_congestion`,
`intel:satellite_crop_health`, `intel:insider_sentiment`

## Configuration Env Vars

| Variable | Default | Description |
|----------|---------|-------------|
| `SCREENER_PROMOTION_THRESHOLD` | `0.65` | Conviction to enter watchlist |
| `SCREENER_DEMOTION_THRESHOLD` | `0.45` | Conviction to exit watchlist |
| `SCREENER_MAX_DYNAMIC_TICKERS` | `50` | Max dynamic watchlist slots |
| `SCREENER_EVICTION_HYSTERESIS` | `0.05` | Min gap required for eviction |
| `SCREENER_STALE_TTL_HOURS` | `72` | Hours before stale force-demote |
| `SCREENER_DECAY_RATE` | `0.995` | Per-cycle conviction decay factor |
| `SCREENER_DECAY_INTERVAL_SECONDS` | `300` | Decay cycle interval (5 min) |
| `SCREENER_CONVERGENCE_WINDOW_MINUTES` | `30` | Multi-source bonus window |
| `SCREENER_CONVERGENCE_MULTIPLIER` | `1.3` | Multi-source bonus factor |
| `SCREENER_AUDIT_FLUSH_SECONDS` | `30` | Audit log flush interval |
| `SCREENER_AUDIT_FLUSH_BATCH_SIZE` | `100` | Audit log flush batch size |
| `CORE_WATCHLIST` | `SPY,QQQ,IWM,DIA,BTC-USD,ETH-USD` | Always-active core tickers |
| `SCREENER_POLL_INTERVAL_SECONDS` | `30` | Intel channel poll interval |
| `SCREENER_PORT` | `8003` | FastAPI HTTP port |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness + key metrics |
| `GET /metrics` | Prometheus scrape |
| `GET /watchlist` | Current watchlist sorted by conviction |
| `GET /watchlist/history` | Last promotion/demotion events |
| `GET /convictions` | All tracked tickers with scores |
| `GET /convictions/{ticker}` | Single ticker conviction detail |
| `GET /stats` | Processing rate, uptime, slot usage |

## Audit Log → Step 7 RL Training

`discovery_audit_log` is a TimescaleDB hypertable. Every record includes:
- `conviction_before`, `conviction_after` — the Bayesian update delta
- `source_channel` — which intel source triggered the update
- `extraction_confidence` — entity extractor certainty
- `likelihood_ratio` — the full LR product (decomposable for attribution)
- `multi_source_bonus` — whether convergence bonus applied
- `payload JSONB` — raw intel value that triggered the update

This gives Step 7 (RL) a fully labeled dataset: **state** (conviction snapshot) + **action** (promotion/demotion decision) + **context** (multi-source signals) with no additional annotation needed.

## Phase 2 / Phase 3 Integration Points

**Phase 2 — Alpaca data spine:**
- `entity_extractor.py` gains a `validate_ticker_live()` call against Alpaca
  to verify a discovered ticker has current tradeable data
- `conviction_scorer.py` gains Alpaca fundamentals channel weight

**Phase 3 — Auto-enrichment:**
- `extract_tickers_tier2()` in `entity_extractor.py` gets wired to Gemini/GPT-4o
  for ambiguous entity resolution (e.g., "the Cupertino company" → AAPL)
- New intel channels (`intel:sec_filings`, `intel:options_flow`, etc.) just need
  entries in `conviction_scorer.SOURCE_WEIGHTS` — no other changes required

## Operational Notes

- **Polling, not pub/sub:** `IntelPublisher.publish()` uses Redis SET, not PUBLISH.
  The screener polls with GET every 30s. Uses per-channel timestamp deduplication
  to avoid re-processing unchanged values.
- **Startup recovery:** Reloads conviction state from `discovery:convictions` hash
  and watchlist from `discovery:watchlist` sorted set on container restart.
- **Archive dir:** `/mnt/archive/discovery/discovery_YYYYMMDD.jsonl`
- **Postgres table:** `discovery_audit_log` (dbmate migration `20260307000003_`)
