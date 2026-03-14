-- migrate:up

CREATE TABLE IF NOT EXISTS intel_dead_letters (
    id            BIGSERIAL PRIMARY KEY,
    service_name  TEXT        NOT NULL,
    channel       TEXT        NOT NULL,
    raw_payload   JSONB       NOT NULL,
    error_message TEXT        NOT NULL,
    error_type    TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dead_letters_service
    ON intel_dead_letters (service_name);

CREATE INDEX IF NOT EXISTS idx_dead_letters_created
    ON intel_dead_letters (created_at);

-- migrate:down

DROP TABLE IF EXISTS intel_dead_letters;
