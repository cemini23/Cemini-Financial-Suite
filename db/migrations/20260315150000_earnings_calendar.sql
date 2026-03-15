-- migrate:up
-- Step 19: Earnings Calendar — prediction accuracy tracking for RL training features

CREATE TABLE IF NOT EXISTS earnings_calendar (
    id              SERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    cik             TEXT NOT NULL,
    estimated_date  DATE,
    actual_date     DATE,          -- filled when 10-Q/10-K filing appears
    filing_type     TEXT,          -- '10-Q' or '10-K'
    status          TEXT NOT NULL,
    confidence      FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, estimated_date)
);

CREATE INDEX IF NOT EXISTS idx_earnings_calendar_estimated
    ON earnings_calendar (estimated_date, status);

CREATE INDEX IF NOT EXISTS idx_earnings_calendar_symbol
    ON earnings_calendar (symbol);

-- migrate:down
DROP TABLE IF EXISTS earnings_calendar;
