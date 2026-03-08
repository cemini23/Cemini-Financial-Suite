-- migrate:up
-- Step 29 — Vector DB Intelligence Layer
-- intel_embeddings: stores text embeddings for all intel messages.
-- Uses pgvector (already enabled by migration 20260307000001).
-- HNSW index for approximate nearest-neighbor at scale.
-- TimescaleDB hypertable for time-based partitioning.

CREATE TABLE IF NOT EXISTS intel_embeddings (
    id             BIGSERIAL,
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_type    VARCHAR(50) NOT NULL,       -- 'x_tweet','gdelt_article','playbook_snapshot','intel_message','discovery_audit'
    source_id      VARCHAR(255),               -- original ID (tweet ID, GDELT URL hash, etc.)
    source_channel VARCHAR(100),               -- intel:* channel name if applicable
    content        TEXT NOT NULL,              -- original text
    embedding      vector(384) NOT NULL,       -- pgvector column (all-MiniLM-L6-v2)
    metadata       JSONB DEFAULT '{}',         -- author, engagement, ticker mentions, etc.
    tickers        VARCHAR(20)[] DEFAULT '{}', -- extracted ticker symbols
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index for fast approximate nearest-neighbor cosine search.
-- m=16 (connections per layer), ef_construction=200 (quality vs build time).
-- Good defaults for up to 5M vectors. ef_search tuned at query time.
CREATE INDEX IF NOT EXISTS idx_intel_embeddings_hnsw
    ON intel_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- Filtered search indexes
CREATE INDEX IF NOT EXISTS idx_intel_embeddings_source
    ON intel_embeddings (source_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_intel_embeddings_tickers
    ON intel_embeddings USING gin (tickers);

CREATE INDEX IF NOT EXISTS idx_intel_embeddings_channel
    ON intel_embeddings (source_channel, timestamp DESC);

-- TimescaleDB hypertable — partitions by day, enables time-range queries at scale.
SELECT create_hypertable(
    'intel_embeddings', 'timestamp',
    if_not_exists  => TRUE,
    migrate_data   => TRUE
);

-- migrate:down
DROP TABLE IF EXISTS intel_embeddings;
