-- migrate:up
-- Step 23: Options Greeks Engine — historical vol surface snapshots
-- Used for RL training data (Step 7): realized vol, vol regime, beta features

CREATE TABLE IF NOT EXISTS vol_surface_log (
    id                  SERIAL PRIMARY KEY,
    timestamp           TIMESTAMPTZ NOT NULL,
    payload             JSONB NOT NULL,
    market_vol_regime   TEXT NOT NULL CHECK (market_vol_regime IN ('LOW', 'NORMAL', 'HIGH')),
    vix                 FLOAT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vol_surface_log_ts
    ON vol_surface_log (timestamp DESC);

-- migrate:down
DROP TABLE IF EXISTS vol_surface_log;
