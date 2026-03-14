-- migrate:up

CREATE TABLE IF NOT EXISTS edgar_fundamentals (
    id               BIGSERIAL PRIMARY KEY,
    ticker           TEXT NOT NULL,
    cik              TEXT NOT NULL,
    period           TEXT NOT NULL,          -- e.g. "CY2024Q4" or "CY2024"
    revenue          NUMERIC,
    net_income       NUMERIC,
    eps              NUMERIC,
    total_assets     NUMERIC,
    total_liabilities NUMERIC,
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cik, period)
);

CREATE INDEX IF NOT EXISTS idx_edgar_fundamentals_ticker ON edgar_fundamentals(ticker);
CREATE INDEX IF NOT EXISTS idx_edgar_fundamentals_period ON edgar_fundamentals(period);

CREATE TABLE IF NOT EXISTS edgar_filings_log (
    id               BIGSERIAL PRIMARY KEY,
    ticker           TEXT NOT NULL,
    cik              TEXT NOT NULL,
    form_type        TEXT NOT NULL,
    accession_number TEXT NOT NULL UNIQUE,
    filed_at         TIMESTAMPTZ,
    filing_url       TEXT,
    processed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_edgar_filings_ticker ON edgar_filings_log(ticker);
CREATE INDEX IF NOT EXISTS idx_edgar_filings_form   ON edgar_filings_log(form_type);
CREATE INDEX IF NOT EXISTS idx_edgar_filings_filed  ON edgar_filings_log(filed_at);

-- migrate:down

DROP TABLE IF EXISTS edgar_filings_log;
DROP TABLE IF EXISTS edgar_fundamentals;
