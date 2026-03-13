-- migrate:up

CREATE TABLE IF NOT EXISTS fred_observations (
    id              BIGSERIAL PRIMARY KEY,
    series_id       TEXT NOT NULL,
    observation_date DATE NOT NULL,
    value           DOUBLE PRECISION,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (series_id, observation_date)
);

CREATE INDEX IF NOT EXISTS idx_fred_obs_series_date
    ON fred_observations (series_id, observation_date DESC);

-- migrate:down

DROP TABLE IF EXISTS fred_observations;
