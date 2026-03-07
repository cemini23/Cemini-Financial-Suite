-- migrate:up
-- pgvector enables storage and similarity search of ML embedding vectors.
-- Required for future semantic search on geopolitical events and trade reasoning.
-- The extension is bundled with the timescale/timescaledb-ha image.
CREATE EXTENSION IF NOT EXISTS vector;

-- migrate:down
DROP EXTENSION IF EXISTS vector;
