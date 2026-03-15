-- migrate:up

CREATE TABLE IF NOT EXISTS discord_alert_log (
    id           SERIAL PRIMARY KEY,
    sent_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_type   TEXT        NOT NULL DEFAULT 'INFO',
    title        TEXT        NOT NULL,
    ticker       TEXT,
    regime       TEXT,
    rotation_bias TEXT,
    http_status  INT,
    enriched     BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_discord_alert_log_sent_at
    ON discord_alert_log (sent_at DESC);

-- migrate:down

DROP TABLE IF EXISTS discord_alert_log;
