-- migrate:up
-- Step 35: TimescaleDB continuous aggregate setup + compression + retention
--
-- raw_market_ticks has a SERIAL PK on `id` which is incompatible with
-- TimescaleDB's requirement that all UNIQUE constraints include the time column.
-- We drop the PK, add a plain index for id lookups, promote to hypertable,
-- then create a 1-min CAGG with explicit non-NULL offsets.

-- 1. Drop integer PK (incompatible with hypertable time-partitioning)
ALTER TABLE raw_market_ticks DROP CONSTRAINT raw_market_ticks_pkey;

-- 2. Retain id lookup performance via a plain (non-unique) index
CREATE INDEX IF NOT EXISTS idx_rmt_id ON raw_market_ticks (id);

-- 3. Promote to hypertable, migrating existing 67K rows into daily chunks
SELECT create_hypertable(
    'raw_market_ticks',
    'timestamp',
    migrate_data        => true,
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists       => true
);

-- 4. Create 1-minute OHLCV continuous aggregate with explicit non-NULL end_offset.
--    WITH NO DATA prevents the initial refresh from moving the watermark to
--    "now" before the policy scheduler takes over, which would leave a gap.
CREATE MATERIALIZED VIEW market_ticks_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', timestamp) AS bucket,
    symbol,
    FIRST(price, timestamp)            AS open,
    MAX(price)                         AS high,
    MIN(price)                         AS low,
    LAST(price, timestamp)             AS close,
    SUM(volume)                        AS volume,
    COUNT(*)                           AS tick_count
FROM raw_market_ticks
GROUP BY bucket, symbol
WITH NO DATA;

-- 5. Refresh policy: keep CAGG current to within 1 minute of real-time.
--    end_offset => INTERVAL '1 minute' (NEVER NULL — prevents staleness bug
--    where NULL end_offset causes the aggregate to stop refreshing at the
--    TimescaleDB internal watermark boundary).
SELECT add_continuous_aggregate_policy(
    'market_ticks_1min',
    start_offset      => INTERVAL '3 days',
    end_offset        => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- 6. Enable columnar compression on the raw hypertable.
--    Segment by symbol so all ticks for a given instrument compress together.
ALTER TABLE raw_market_ticks SET (
    timescaledb.compress,
    timescaledb.compress_orderby  = 'timestamp DESC',
    timescaledb.compress_segmentby = 'symbol'
);

-- 7. Compression policy: compress raw chunks older than 7 days.
SELECT add_compression_policy('raw_market_ticks', INTERVAL '7 days');

-- 8. Retention policy: drop raw tick chunks older than 90 days.
--    Compressed CAGG data is kept indefinitely (no retention on market_ticks_1min).
SELECT add_retention_policy('raw_market_ticks', INTERVAL '90 days');

-- migrate:down
-- NOTE: Cannot safely revert a hypertable to a plain table without data loss.
-- Down migration removes policies and the CAGG view, leaves hypertable in place.

SELECT remove_retention_policy('raw_market_ticks',   if_exists => true);
SELECT remove_compression_policy('raw_market_ticks', if_exists => true);
DROP MATERIALIZED VIEW IF EXISTS market_ticks_1min CASCADE;
