-- migrate:up

-- ──────────────────────────────────────────────────────────────────────────────
-- audit_hash_chain
-- SHA-256 hash chain for tamper-evident trade audit trail (Step 43).
-- Each row stores the hash of the previous row — modifying any historical
-- entry invalidates all subsequent hashes.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_hash_chain (
    id                  UUID            PRIMARY KEY,      -- UUIDv7 monotonic
    sequence_num        BIGSERIAL       NOT NULL,         -- gap-detectable sequence
    source_table        TEXT            NOT NULL,          -- trade_history | ai_trade_logs | playbook_logs
    source_id           TEXT            NOT NULL,          -- PK from source table
    payload_canonical   TEXT            NOT NULL,          -- canonicalized JSON (sort_keys, no spaces)
    payload_hash        TEXT            NOT NULL,          -- SHA-256 of payload_canonical
    prev_hash           TEXT            NOT NULL,          -- chain_hash of previous entry ('0'*64 for genesis)
    chain_hash          TEXT            NOT NULL,          -- SHA-256(prev_hash || payload_hash)
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_chain_source   ON audit_hash_chain (source_table, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_chain_sequence ON audit_hash_chain (sequence_num);

-- ──────────────────────────────────────────────────────────────────────────────
-- PL/pgSQL BEFORE INSERT trigger
-- Computes chain_hash from the previous entry on each INSERT.
-- Modifying any historical prev_hash/chain_hash invalidates the chain.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION audit_chain_hash_trigger() RETURNS TRIGGER AS $$
DECLARE
    last_hash TEXT;
BEGIN
    -- Find the chain_hash of the most recent entry
    SELECT chain_hash INTO last_hash
    FROM audit_hash_chain
    ORDER BY sequence_num DESC
    LIMIT 1;

    -- Genesis entry uses 64 zero chars as prev_hash
    IF last_hash IS NULL THEN
        NEW.prev_hash := repeat('0', 64);
    ELSE
        NEW.prev_hash := last_hash;
    END IF;

    -- chain_hash = SHA-256(prev_hash || payload_hash)
    NEW.chain_hash := encode(
        sha256((NEW.prev_hash || NEW.payload_hash)::bytea),
        'hex'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_chain_hash
BEFORE INSERT ON audit_hash_chain
FOR EACH ROW EXECUTE FUNCTION audit_chain_hash_trigger();

-- ──────────────────────────────────────────────────────────────────────────────
-- audit_batch_commitments
-- Daily Merkle tree batch commitments (Layer 2).
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_batch_commitments (
    id              UUID            PRIMARY KEY,
    batch_date      DATE            NOT NULL UNIQUE,
    merkle_root     TEXT            NOT NULL,
    entry_count     INTEGER         NOT NULL,
    first_entry_id  UUID,
    last_entry_id   UUID,
    first_sequence  BIGINT,
    last_sequence   BIGINT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_batch_date ON audit_batch_commitments (batch_date);

-- ──────────────────────────────────────────────────────────────────────────────
-- audit_intent_log
-- Pre-evaluation intent entries (proves no cherry-picking).
-- Logged BEFORE the signal detector runs.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_intent_log (
    id              UUID            PRIMARY KEY,    -- UUIDv7
    signal_source   TEXT            NOT NULL,        -- e.g. 'playbook', 'screener'
    signal_type     TEXT            NOT NULL,        -- e.g. 'EpisodicPivot'
    ticker          TEXT,
    intent_hash     TEXT            NOT NULL,        -- SHA-256 of canonicalized intent
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_intent_created ON audit_intent_log (created_at);
CREATE INDEX IF NOT EXISTS idx_audit_intent_source  ON audit_intent_log (signal_source, signal_type);

-- migrate:down
DROP TRIGGER IF EXISTS trg_audit_chain_hash ON audit_hash_chain;
DROP FUNCTION IF EXISTS audit_chain_hash_trigger;
DROP TABLE IF EXISTS audit_intent_log;
DROP TABLE IF EXISTS audit_batch_commitments;
DROP TABLE IF EXISTS audit_hash_chain;
