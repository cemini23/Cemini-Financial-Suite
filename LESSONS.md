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

**flake8 config**
E501 ignored, max-line-length=120. E999 and F821 enforced. E741 (ambiguous var names) enforced.
Never add E501 enforcement. Rename l/O/I to ln/val/idx.

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
