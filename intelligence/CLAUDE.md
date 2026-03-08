# intelligence/ — Vector DB Intelligence Layer (Step 29)

## Purpose

Semantic memory for the Cemini Financial Suite. Converts text intel into 384-dim
embeddings stored in pgvector (on the existing Postgres/TimescaleDB instance), enabling:

1. **Similarity search** — "What similar X tweets did we see before $TSLA spiked?"
2. **CRAG retrieval** — grade retrieved context before injecting into LLM (Step 7)
3. **Historical enrichment** — when a ticker is promoted to the watchlist, retrieve the
   3 most similar historical intel records as context for the conviction scorer

## Architecture

```
intel:* channels (Redis)
        │
        ▼
EmbeddingWorker (realtime_worker.py)   ← psubscribe to all intel:*
        │  batch every 10s / 32 msgs
        ▼
embedder.embed_batch()                 ← sentence-transformers (CPU, lazy)
        │
        ▼
vector_store.store_embeddings_batch()  ← psycopg2 → intel_embeddings (pgvector)
        │                                HNSW index (m=16, ef_construction=200)
        ▼
retriever.retrieve_context()           ← CRAG pattern (retrieve→grade→correct)
        │
        ▼
Step 7 RL Training Loop (future)       ← LLM gets graded context for decisions
```

## Embedding Model

- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (MIT license)
- **Dimensions:** 384
- **Size:** ~80MB cached in `~/.cache/huggingface/`
- **Speed:** ~200-500 texts/second on CPU
- **Lazy loading:** model is NOT loaded at import time — only on first `embed()` call
- **Config:** override via `EMBEDDING_MODEL` env var

## Database Table: `intel_embeddings`

| Column         | Type              | Purpose                                      |
|----------------|-------------------|----------------------------------------------|
| id             | BIGSERIAL PK      | Auto-incrementing row ID                     |
| timestamp      | TIMESTAMPTZ       | When the intel was originally published      |
| source_type    | VARCHAR(50)       | 'x_tweet','gdelt_article','playbook_snapshot','intel_message','discovery_audit' |
| source_id      | VARCHAR(255)      | Original ID (tweet ID, URL hash, etc.)       |
| source_channel | VARCHAR(100)      | intel:* channel name if from Redis           |
| content        | TEXT              | Original text that was embedded              |
| embedding      | vector(384)       | pgvector column                              |
| metadata       | JSONB             | author, engagement, ticker mentions, etc.    |
| tickers        | VARCHAR(20)[]     | Extracted ticker symbols (GIN indexed)       |

**Indexes:**
- HNSW on `embedding vector_cosine_ops` (m=16, ef_construction=200) — fast ANN
- GIN on `tickers` — fast ANY(tickers) filter
- B-tree on `(source_type, timestamp DESC)` — time-range filtered searches
- Partial UNIQUE on `(source_type, source_id) WHERE source_id IS NOT NULL` — dedup

## The Killer Query

pgvector on the same Postgres instance as TimescaleDB time-series data means you can
JOIN similarity search with market state in a **single SQL statement**:

```sql
SELECT ie.content, 1 - (ie.embedding <=> $1::vector) AS sim,
       rmt.close, rmt.volume, rmt.rsi
FROM intel_embeddings ie
LEFT JOIN LATERAL (
    SELECT close, volume, rsi FROM raw_market_ticks
    WHERE timestamp <= ie.timestamp AND ticker = ANY(ie.tickers)
    ORDER BY timestamp DESC LIMIT 1
) rmt ON true
ORDER BY ie.embedding <=> $1::vector
LIMIT 10;
```

No standalone Qdrant/Weaviate/Pinecone can do this JOIN. This is the query that
makes a technical buyer say "that's architecturally elegant."

API endpoint: `POST /vectors/search_with_market`

## CRAG Retrieval Pattern

`retriever.retrieve_context()` implements Corrective RAG:

1. **Retrieve** — fetch 2× requested docs, min_similarity=0.5
2. **Grade** each doc:
   - `RELEVANT` ≥ 0.7 cosine similarity
   - `AMBIGUOUS` 0.5–0.7
   - `IRRELEVANT` < 0.5
3. **Correct**:
   - All RELEVANT → `quality="high"`
   - Mix → keep RELEVANT, try re-search with tighter filters; `quality="mixed"`
   - All IRRELEVANT → empty list, `quality="insufficient"` (never hallucinate)
4. **Return** `RetrievalResult` with graded contexts for Step 7 LLM injection

## Redis Channels Consumed

The `EmbeddingWorker` subscribes to **all** `intel:*` channels via `psubscribe`:
- `intel:playbook_snapshot` — regime + signal context
- `intel:spy_trend`, `intel:vix_level` — macro market state
- `intel:social_score`, `intel:geo_risk_score` — alt data signals
- `intel:discovery_snapshot` — watchlist conviction updates
- All others: buffered, embedded, stored as `source_type=intel_message`

## Seeder CLI

One-time bulk import of pre-existing archives:

```bash
# X harvester corpus (~15,600 tweets, CPU-bound, ~5-10 min)
python3 intelligence/seeder.py --source x_tweets
# Or with custom path:
python3 intelligence/seeder.py --source x_tweets --archive-dir /mnt/archive/x_research/

# GDELT intel (if archive exists)
python3 intelligence/seeder.py --source gdelt --archive-dir /mnt/archive/gdelt/

# All sources sequentially
python3 intelligence/seeder.py --all
```

Progress is logged every 500 records. The seeder is idempotent — `ON CONFLICT DO NOTHING`
on `(source_type, source_id)` so re-runs are safe.

## API Endpoints (on port 8003)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/vectors/stats` | Total embeddings, breakdown by source type |
| POST | `/vectors/search` | Body: `{query, limit?, source_type?, tickers?, since?}` |
| POST | `/vectors/search_with_market` | Same + market state JOIN |
| GET | `/vectors/similar/{source_type}/{source_id}` | Find docs similar to a stored doc |
| POST | `/vectors/embed` | Manually embed and store text |

## Step 7 Integration Path

When the RL training loop (Step 7) is implemented:
1. The orchestrator evaluates a trade signal
2. `retriever.retrieve_context(f"trade signal for {ticker}", tickers=[ticker])` is called
3. The `RetrievalResult.contexts` (graded, relevant historical intel) are injected into
   the LLM debate prompt as few-shot context
4. The LLM decision is grounded in actual historical patterns, not zero-shot

## Upgrade Path

pgvector handles up to ~5M vectors efficiently with the HNSW index at these settings.
If the corpus grows beyond that:
1. Increase `m` and `ef_construction` in the HNSW index
2. Or migrate to a dedicated Qdrant instance:
   - Same embedding model (384-dim vectors are portable)
   - Same CRAG retrieval logic (swap the `search_similar` call)
   - Lose the TimescaleDB JOIN (trade accuracy for scale)

## Key Config Env Vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace model ID |
| `EMBEDDING_DIM` | `384` | Vector dimensions |
| `VECTOR_SEARCH_EF` | `100` | HNSW ef_search (quality vs speed) |
| `VECTOR_MIN_SIMILARITY` | `0.5` | Default minimum cosine similarity |
| `VECTOR_CRAG_RELEVANT_THRESHOLD` | `0.7` | CRAG RELEVANT grade cutoff |
| `VECTOR_REALTIME_BUFFER_SIZE` | `32` | Max messages before forced flush |
| `VECTOR_REALTIME_FLUSH_SECONDS` | `10` | Time-based flush interval |
