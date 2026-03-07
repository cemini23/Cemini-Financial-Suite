-- migrate:up

-- ──────────────────────────────────────────────────────────────────────────────
-- Extensions
-- ──────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ──────────────────────────────────────────────────────────────────────────────
-- ai_trade_logs
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_trade_logs (
    symbol      VARCHAR,
    action      VARCHAR,
    verdict     VARCHAR,
    confidence  DOUBLE PRECISION,
    size        DOUBLE PRECISION,
    reasoning   TEXT,
    timestamp   TIMESTAMPTZ
);

-- ──────────────────────────────────────────────────────────────────────────────
-- geopolitical_logs
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS geopolitical_logs (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_date      TIMESTAMPTZ,
    source_url      TEXT,
    source_domain   TEXT,
    title           TEXT,
    cameo_code      VARCHAR,
    cameo_category  VARCHAR,
    goldstein_scale DOUBLE PRECISION,
    avg_tone        DOUBLE PRECISION,
    num_sources     INTEGER,
    num_articles    INTEGER,
    actor1_country  VARCHAR,
    actor2_country  VARCHAR,
    action_geo      VARCHAR,
    risk_score      DOUBLE PRECISION,
    risk_level      VARCHAR,
    themes          JSONB,
    payload         JSONB
);

CREATE INDEX IF NOT EXISTS idx_geo_logs_cameo   ON geopolitical_logs (cameo_code);
CREATE INDEX IF NOT EXISTS idx_geo_logs_created ON geopolitical_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_geo_logs_risk    ON geopolitical_logs (risk_score);

-- ──────────────────────────────────────────────────────────────────────────────
-- macro_logs
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS macro_logs (
    timestamp   TIMESTAMPTZ,
    fg_index    DOUBLE PRECISION,
    yield_10y   DOUBLE PRECISION
);

-- ──────────────────────────────────────────────────────────────────────────────
-- playbook_logs
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS playbook_logs (
    id          BIGSERIAL PRIMARY KEY,
    timestamp   TIMESTAMPTZ NOT NULL,
    log_type    VARCHAR     NOT NULL,
    regime      VARCHAR,
    payload     JSONB       NOT NULL
);

-- ──────────────────────────────────────────────────────────────────────────────
-- portfolio_summary
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolio_summary (
    symbol          VARCHAR,
    entry_price     DOUBLE PRECISION,
    current_price   DOUBLE PRECISION,
    market_value    DOUBLE PRECISION,
    is_cash         BOOLEAN,
    timestamp       TIMESTAMPTZ
);

-- ──────────────────────────────────────────────────────────────────────────────
-- raw_market_ticks
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw_market_ticks (
    id          SERIAL PRIMARY KEY,
    symbol      VARCHAR     NOT NULL,
    price       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION,
    timestamp   TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ──────────────────────────────────────────────────────────────────────────────
-- sentiment_logs
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sentiment_logs (
    timestamp       TIMESTAMPTZ,
    symbol          VARCHAR,
    sentiment_score DOUBLE PRECISION,
    source          VARCHAR
);

-- ──────────────────────────────────────────────────────────────────────────────
-- trade_history
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trade_history (
    timestamp   TIMESTAMPTZ,
    symbol      VARCHAR,
    action      VARCHAR,
    price       DOUBLE PRECISION,
    reason      TEXT,
    rsi         DOUBLE PRECISION,
    strategy    VARCHAR
);

-- ──────────────────────────────────────────────────────────────────────────────
-- v_correlation_metrics (view)
-- Computes hourly-bucketed Pearson correlation between symbol price pairs.
-- ──────────────────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_correlation_metrics;
CREATE VIEW v_correlation_metrics AS
WITH price_series AS (
    SELECT
        date_trunc('hour', timestamp) AS hour,
        symbol,
        avg(price) AS avg_price
    FROM trade_history
    WHERE price IS NOT NULL
    GROUP BY date_trunc('hour', timestamp), symbol
),
pairs AS (
    SELECT DISTINCT
        a.symbol AS sym_a,
        b.symbol AS sym_b
    FROM price_series a
    CROSS JOIN price_series b
    WHERE a.symbol < b.symbol
),
corr_calc AS (
    SELECT
        p.sym_a || '/' || p.sym_b AS pair,
        corr(a.avg_price, b.avg_price) AS coefficient,
        count(*) AS data_points
    FROM pairs p
    JOIN price_series a ON a.symbol = p.sym_a
    JOIN price_series b ON b.symbol = p.sym_b AND b.hour = a.hour
    GROUP BY p.sym_a || '/' || p.sym_b
    HAVING count(*) >= 5
)
SELECT
    pair,
    round(coefficient::numeric, 4) AS coefficient,
    data_points
FROM corr_calc;

-- migrate:down

DROP VIEW  IF EXISTS v_correlation_metrics CASCADE;
DROP TABLE IF EXISTS trade_history;
DROP TABLE IF EXISTS sentiment_logs;
DROP TABLE IF EXISTS raw_market_ticks;
DROP TABLE IF EXISTS portfolio_summary;
DROP TABLE IF EXISTS playbook_logs;
DROP TABLE IF EXISTS macro_logs;
DROP INDEX IF EXISTS idx_geo_logs_risk;
DROP INDEX IF EXISTS idx_geo_logs_created;
DROP INDEX IF EXISTS idx_geo_logs_cameo;
DROP TABLE IF EXISTS geopolitical_logs;
DROP TABLE IF EXISTS ai_trade_logs;
