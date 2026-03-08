"""Vector DB Intelligence Layer — Step 29.

Provides semantic memory for the Cemini intelligence-in architecture:
  - embedder.py      : Text → 384-dim vector (all-MiniLM-L6-v2, lazy load)
  - vector_store.py  : pgvector CRUD (psycopg2, HNSW index)
  - retriever.py     : CRAG retrieval pattern (retrieve → grade → correct → format)
  - seeder.py        : Bulk import from X harvester / GDELT / playbook / discovery
  - realtime_worker.py: Redis intel:* subscriber → batch embed → store
  - config.py        : All settings via env vars
"""
