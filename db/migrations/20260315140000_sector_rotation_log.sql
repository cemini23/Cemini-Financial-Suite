-- migrate:up
-- Step 25: Sector Rotation Monitor — historical rotation snapshots
-- Used for RL training data (Step 7) and backtesting sector momentum strategies

CREATE TABLE IF NOT EXISTS sector_rotation_log (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    lookback_days   INT NOT NULL,
    payload         JSONB NOT NULL,
    rotation_bias   TEXT NOT NULL CHECK (rotation_bias IN ('RISK_ON', 'RISK_OFF', 'NEUTRAL')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sector_rotation_log_ts_lookback
    ON sector_rotation_log (timestamp, lookback_days);

-- migrate:down
DROP TABLE IF EXISTS sector_rotation_log;
