# GDELT Geopolitical Data

The GDELT (Global Database of Events, Language, and Tone) pipeline harvests geopolitical event data from the GDELT Global Knowledge Graph (GKG) and converts it into quantitative market signals.

---

## Role

- Monitor global news events for geopolitical risk signals
- Detect escalating conflict, trade tensions, sanctions, and political instability
- Publish geopolitical risk scores to the Intel Bus for regime context
- Feed the Opportunity Screener for sector-level impact analysis

---

## gdelt_harvester Service

The `gdelt_harvester` polls the GDELT GKG API every 15 minutes. GDELT is entirely free and open — no API key required. It indexes over 100 news sources in real-time.

**Key Python package:** `gdeltdoc` (PyPI name is `gdeltdoc`, **not** `gdelt-doc-api` — a known gotcha that fails pip-audit).

---

## Signal Construction

GDELT assigns a "Goldstein Scale" score (−10 to +10) to each event, where negative scores indicate conflict/tension and positive scores indicate cooperation. The harvester:

1. Fetches events related to tracked tickers and sectors
2. Aggregates Goldstein scores weighted by source credibility
3. Normalizes to a 0.0–1.0 sentiment scale
4. Publishes to `intel:geopolitical`

---

## JSONL Archive

Every 15-minute harvest is archived to `/mnt/archive/geopolitical/gdelt_YYYYMMDD_HHMM.jsonl`.

---

## Intel Bus Output

```
intel:geopolitical → {
    "risk_score": 0.32,         # 0.0 = high risk, 1.0 = low risk
    "top_events": [...],        # top 5 events by volume
    "sectors_affected": [...],  # energy, defense, tech, etc.
    "fetched_at": "2026-03-14T14:15:00Z"
}
TTL: 900s (15 min)
```

---

## Conviction Score Contribution

GDELT signals carry a weight of **0.45** in the Opportunity Screener's Bayesian conviction scorer — moderate weight. Geopolitical signals are useful for sector-level context (energy, defense, commodities) but are noisy predictors of individual stock moves.
