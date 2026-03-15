-- migrate:up

CREATE TABLE IF NOT EXISTS debate_sessions (
    id               UUID PRIMARY KEY,
    ticker           TEXT NOT NULL,
    regime           TEXT NOT NULL,
    verdict          TEXT NOT NULL,
    confidence       NUMERIC NOT NULL,
    bull_score       NUMERIC NOT NULL,
    bear_score       NUMERIC NOT NULL,
    tie_break_used   BOOLEAN NOT NULL DEFAULT FALSE,
    phase_count      INTEGER NOT NULL DEFAULT 5,
    payload          JSONB NOT NULL,
    started_at       TIMESTAMPTZ NOT NULL,
    completed_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_debate_sessions_ticker  ON debate_sessions(ticker, created_at);
CREATE INDEX IF NOT EXISTS idx_debate_sessions_verdict ON debate_sessions(verdict, created_at);
CREATE INDEX IF NOT EXISTS idx_debate_sessions_regime  ON debate_sessions(regime, created_at);

-- migrate:down

DROP TABLE IF EXISTS debate_sessions;
