"""intelligence/config.py — Configuration via environment variables (Step 29i)."""
from __future__ import annotations

import os

# ── Embedding Model ───────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# ── Vector Search ─────────────────────────────────────────────────────────────
VECTOR_SEARCH_EF = int(os.getenv("VECTOR_SEARCH_EF", "100"))         # HNSW ef_search quality
VECTOR_MIN_SIMILARITY = float(os.getenv("VECTOR_MIN_SIMILARITY", "0.5"))

# ── CRAG Thresholds ───────────────────────────────────────────────────────────
VECTOR_CRAG_RELEVANT_THRESHOLD = float(os.getenv("VECTOR_CRAG_RELEVANT_THRESHOLD", "0.7"))
VECTOR_CRAG_AMBIGUOUS_THRESHOLD = float(os.getenv("VECTOR_CRAG_AMBIGUOUS_THRESHOLD", "0.5"))

# ── Batch & Real-Time ─────────────────────────────────────────────────────────
VECTOR_BATCH_SIZE = int(os.getenv("VECTOR_BATCH_SIZE", "64"))
VECTOR_REALTIME_BUFFER_SIZE = int(os.getenv("VECTOR_REALTIME_BUFFER_SIZE", "32"))
VECTOR_REALTIME_FLUSH_SECONDS = int(os.getenv("VECTOR_REALTIME_FLUSH_SECONDS", "10"))

# ── Database ──────────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "qdb")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quest")  # nosemgrep: semgrep.hardcoded-env-default-credential

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")  # nosemgrep: semgrep.hardcoded-env-default-credential
