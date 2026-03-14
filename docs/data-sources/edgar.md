# SEC EDGAR Direct Pipeline

Step 40 built a direct integration with the SEC EDGAR free API, eliminating the previous $49/month sec-api.io dependency. The `edgar_pipeline` service provides filings monitoring, Form 4 insider trade tracking, and XBRL fundamental data.

---

## Role

- Monitor SEC EDGAR for new filings (10-K, 10-Q, 8-K) across tracked tickers
- Parse Form 4 insider transactions (buy/sell by executives and directors)
- Harvest XBRL financial fundamentals for quantitative analysis

---

## Three APScheduler Jobs

| Job | Interval | Table | Intel Key |
|---|---|---|---|
| Filing monitor | Every 10 min | `edgar_filings_log` | `intel:edgar_filing` |
| Form 4 insider | Every 30 min | (in edgar_filings_log) | `intel:edgar_insider` |
| XBRL fundamentals | Daily 06:00 UTC | `edgar_fundamentals` | — |

---

## Ticker-to-CIK Mapping

The EDGAR API uses CIK (Central Index Key) numbers, not ticker symbols. `scrapers/edgar/cik_mapping.py` provides a local lookup table and auto-fetches missing CIKs from the EDGAR company search API.

**Important:** ETFs (e.g., IWM, SPY) have no direct SEC CIK because they are not SEC registrants. The pipeline logs a WARNING and skips gracefully when a CIK lookup fails for an ETF.

---

## Form 4 Parsing

Form 4 XML is parsed using `xml.etree.ElementTree`. The XML is sourced directly from SEC EDGAR (a government-published document), so the `# noqa: S314` comment bypasses Bandit's XML injection warning — this is intentional and documented.

---

## Redis Deduplication

Each filing is deduped by accession number:

```
Key: edgar:{filing|form4}:seen:{accession_number}
TTL: 7 days
```

This prevents double-processing when the APScheduler job overlaps with a slow EDGAR response.

---

## Database Schema

```sql
-- Filing log with UNIQUE constraint on accession_number
CREATE TABLE edgar_filings_log (
    id               SERIAL PRIMARY KEY,
    accession_number TEXT UNIQUE NOT NULL,
    cik              TEXT,
    ticker           TEXT,
    form_type        TEXT,
    filed_at         TIMESTAMPTZ,
    content          JSONB,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- XBRL fundamentals with UNIQUE on cik + period
CREATE TABLE edgar_fundamentals (
    id         SERIAL PRIMARY KEY,
    cik        TEXT NOT NULL,
    ticker     TEXT,
    period     TEXT NOT NULL,
    revenue    NUMERIC,
    net_income NUMERIC,
    eps        NUMERIC,
    fetched_at TIMESTAMPTZ,
    UNIQUE (cik, period)
);
```

---

## Conviction Score Contribution

Insider buy transactions from Form 4 carry a weight of **0.85** in the Opportunity Screener's Bayesian conviction scorer — the highest weight of any data source. Direct insider purchases are a leading indicator that management believes the stock is undervalued.
