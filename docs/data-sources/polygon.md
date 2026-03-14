# Market Data — Polygon.io

Polygon.io provides the real-time WebSocket tick feed and serves as the primary market data spine for equities and crypto.

---

## Role

- Real-time trade and quote ticks via WebSocket (`polygon_feed` service)
- Historical OHLCV bars for RSI and signal detection (via Alpaca bridge in QuantOS)
- Tick data stored in `raw_market_ticks` (TimescaleDB hypertable)

---

## polygon_feed Service

The `polygon_feed` service connects to Polygon's WebSocket API and streams incoming ticks directly to:
- `raw_market_ticks` PostgreSQL table (TimescaleDB hypertable with CAGG)
- Redis Intel Bus for real-time consumers

**Key implementation note:** Polygon free-tier bar close timestamps can be hours behind real time. The platform orders tick data by `created_at` (insertion time) rather than `timestamp` (bar close time) to avoid ordering anomalies.

---

## TimescaleDB Schema

```sql
CREATE TABLE raw_market_ticks (
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol      TEXT NOT NULL,
    price       NUMERIC(18, 8) NOT NULL,
    volume      NUMERIC(18, 8),
    source      TEXT DEFAULT 'polygon'
);

-- Hypertable (Step 35 extension)
SELECT create_hypertable('raw_market_ticks', 'created_at');

-- 1-minute CAGG rollup
CREATE MATERIALIZED VIEW market_ticks_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', created_at) AS bucket,
    symbol,
    first(price, created_at) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, created_at) AS close,
    sum(volume) AS volume
FROM raw_market_ticks
GROUP BY bucket, symbol;
```

**Retention policy:** 90 days. **Compression policy:** Chunks older than 7 days are compressed automatically.

---

## Data Quality Notes

- Polygon free tier does not provide Level 2 order book data
- Weekend and after-hours data may have reduced tick frequency
- Crypto data (BTC, ETH) is available 24/7 via Polygon
- The `polygon_feed` service reconnects automatically on WebSocket disconnection
