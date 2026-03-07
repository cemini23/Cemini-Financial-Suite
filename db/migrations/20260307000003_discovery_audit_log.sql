-- migrate:up

-- ──────────────────────────────────────────────────────────────────────────────
-- discovery_audit_log — Step 26.1f (Opportunity Discovery Engine)
-- TimescaleDB hypertable for RL training data (Step 7).
-- Every conviction update, promotion, demotion, eviction, and decay is recorded.
-- ──────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS discovery_audit_log (
    id                   BIGSERIAL,
    timestamp            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ticker               VARCHAR(20) NOT NULL,
    action               VARCHAR(20) NOT NULL,    -- 'conviction_update','promoted','demoted','evicted','decayed'
    conviction_before    FLOAT,
    conviction_after     FLOAT,
    source_channel       VARCHAR(100),
    extraction_confidence FLOAT,
    likelihood_ratio     FLOAT,
    multi_source_bonus   BOOLEAN DEFAULT FALSE,
    payload              JSONB,
    watchlist_size       INT
);

SELECT create_hypertable('discovery_audit_log', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_discovery_audit_ticker
    ON discovery_audit_log (ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_discovery_audit_action
    ON discovery_audit_log (action, timestamp DESC);

-- migrate:down
DROP TABLE IF EXISTS discovery_audit_log;
