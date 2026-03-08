"""intelligence/embedder.py — Text → vector embedding pipeline (Step 29a).

Uses sentence-transformers/all-MiniLM-L6-v2:
  - 384 dimensions, MIT license, ~80MB on disk
  - Fast enough for real-time intel embedding on CPU
  - Cached in ~/.cache/huggingface/ after first download

Model is lazily loaded on first call to embed() so container startup is not blocked.
Log the load time once; subsequent calls are fast (~1-3ms per text on CPU).
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer  # noqa: N814

logger = logging.getLogger("intelligence.embedder")

# ── Module-level singleton (lazy) ─────────────────────────────────────────────
_model: "SentenceTransformer | None" = None  # noqa: UP037


def _get_model() -> "SentenceTransformer":  # noqa: UP037
    """Load model on first call; return cached model on subsequent calls."""
    global _model
    if _model is not None:
        return _model

    from intelligence.config import EMBEDDING_MODEL
    from sentence_transformers import SentenceTransformer

    logger.info("⚙️  Loading embedding model '%s' (first call)…", EMBEDDING_MODEL)
    t0 = time.monotonic()
    _model = SentenceTransformer(EMBEDDING_MODEL)
    elapsed = time.monotonic() - t0
    logger.info("✅ Embedding model loaded in %.2fs", elapsed)
    return _model


def embed(text: str) -> list[float]:
    """Embed a single text string into a 384-dim vector (cosine-normalised)."""
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_batch(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Embed multiple texts efficiently in batches. Returns [] for empty input."""
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def is_model_loaded() -> bool:
    """Return True if the embedding model singleton has been initialised."""
    return _model is not None


def reset_model() -> None:
    """Reset the model singleton (for testing only)."""
    global _model
    _model = None
