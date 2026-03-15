-- migrate:up

CREATE TABLE IF NOT EXISTS edgar_alerts (
    id               UUID PRIMARY KEY,
    ticker           TEXT NOT NULL,
    alert_type       TEXT NOT NULL,
    significance_score INTEGER NOT NULL,
    summary          TEXT NOT NULL,
    filing_url       TEXT,
    payload          JSONB NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_edgar_alerts_ticker ON edgar_alerts(ticker, created_at);
CREATE INDEX IF NOT EXISTS idx_edgar_alerts_score  ON edgar_alerts(significance_score DESC);
CREATE INDEX IF NOT EXISTS idx_edgar_alerts_type   ON edgar_alerts(alert_type, created_at);

-- migrate:down

DROP TABLE IF EXISTS edgar_alerts;
