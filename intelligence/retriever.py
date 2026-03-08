"""intelligence/retriever.py — CRAG Retrieval Pattern (Step 29d).

Corrective Retrieval-Augmented Generation:
  1. Retrieve  — top-K similar docs from pgvector (fetch 2× for headroom)
  2. Grade     — RELEVANT (≥0.7) | AMBIGUOUS (0.5–0.7) | IRRELEVANT (<0.5)
  3. Correct   — refine AMBIGUOUS with tighter filters; discard IRRELEVANT
  4. Format    — structured GradedContext list for LLM injection (Step 7 RL)

retrieval_quality:
  "high"         — enough RELEVANT results to fill max_results
  "mixed"        — some RELEVANT + AMBIGUOUS, or only AMBIGUOUS
  "insufficient" — all IRRELEVANT; returns empty list (never hallucinate)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from cemini_contracts.vector import GradedContext, RetrievalResult
from intelligence import config
from intelligence.embedder import embed
from intelligence.vector_store import search_similar

logger = logging.getLogger("intelligence.retriever")

_RELEVANT = "RELEVANT"
_AMBIGUOUS = "AMBIGUOUS"
_IRRELEVANT = "IRRELEVANT"


def _grade(similarity: float) -> str:
    if similarity >= config.VECTOR_CRAG_RELEVANT_THRESHOLD:
        return _RELEVANT
    if similarity >= config.VECTOR_CRAG_AMBIGUOUS_THRESHOLD:
        return _AMBIGUOUS
    return _IRRELEVANT


def _doc_to_graded(doc: dict, grade: str) -> GradedContext:
    return GradedContext(
        content=doc["content"],
        similarity_score=doc["similarity_score"],
        grade=grade,  # type: ignore[arg-type]
        source_type=doc["source_type"],
        source_id=doc.get("source_id"),
        metadata=doc.get("metadata", {}),
        tickers=doc.get("tickers", []),
        timestamp=doc.get("timestamp"),
    )


def retrieve_context(
    query: str,
    max_results: int = 5,
    source_types: list[str] | None = None,
    tickers: list[str] | None = None,
    recency_hours: int | None = None,
) -> RetrievalResult:
    """CRAG retrieval: retrieve → grade → correct → format.

    Returns structured context suitable for injection into an LLM prompt
    (for Step 7 RL training loop). Never raises — returns insufficient on error.
    """
    try:
        return _retrieve_context_inner(query, max_results, source_types, tickers, recency_hours)
    except Exception as exc:
        logger.warning("retrieve_context error: %s", exc)
        return RetrievalResult(contexts=[], total_retrieved=0, total_relevant=0, retrieval_quality="insufficient")


def _retrieve_context_inner(
    query: str,
    max_results: int,
    source_types: list[str] | None,
    tickers: list[str] | None,
    recency_hours: int | None,
) -> RetrievalResult:
    since = None
    if recency_hours:
        since = datetime.now(timezone.utc) - timedelta(hours=recency_hours)

    # Step 1: Retrieve — fetch 2× requested to allow for grading headroom
    fetch_k = max_results * 2
    query_vec = embed(query)

    if source_types:
        # Search each source type separately then merge (deduplicated by id)
        raw: list[dict] = []
        seen_ids: set[int] = set()
        for st in source_types:
            results = search_similar(
                query_vec,
                limit=fetch_k,
                source_type=st,
                tickers=tickers,
                since=since,
                min_similarity=config.VECTOR_CRAG_AMBIGUOUS_THRESHOLD,
            )
            for r in results:
                if r["id"] not in seen_ids:
                    raw.append(r)
                    seen_ids.add(r["id"])
    else:
        raw = search_similar(
            query_vec,
            limit=fetch_k,
            tickers=tickers,
            since=since,
            min_similarity=config.VECTOR_CRAG_AMBIGUOUS_THRESHOLD,
        )

    total_retrieved = len(raw)

    # Step 2: Grade each retrieved document
    graded_all = [_doc_to_graded(doc, _grade(doc["similarity_score"])) for doc in raw]
    relevant = [g for g in graded_all if g.grade == _RELEVANT]
    ambiguous = [g for g in graded_all if g.grade == _AMBIGUOUS]

    # Step 3: Correct
    if relevant:
        # Attempt to rescue AMBIGUOUS via tighter re-search when ticker context available
        if ambiguous and tickers:
            refined = search_similar(
                query_vec,
                limit=max_results,
                tickers=tickers,
                since=since,
                min_similarity=config.VECTOR_CRAG_RELEVANT_THRESHOLD,
            )
            existing_contents = {g.content for g in relevant}
            for doc in refined:
                if (
                    doc["similarity_score"] >= config.VECTOR_CRAG_RELEVANT_THRESHOLD
                    and doc["content"] not in existing_contents
                ):
                    relevant.append(_doc_to_graded(doc, _RELEVANT))
                    existing_contents.add(doc["content"])

        contexts = relevant[:max_results]
        quality = "high" if len(relevant) >= max_results else "mixed"

    elif ambiguous:
        contexts = ambiguous[:max_results]
        quality = "mixed"

    else:
        # All IRRELEVANT — do not hallucinate, return empty with flag
        logger.debug("retrieve_context: no relevant results for query='%s…'", query[:60])
        contexts = []
        quality = "insufficient"

    return RetrievalResult(
        contexts=contexts,
        total_retrieved=total_retrieved,
        total_relevant=len(relevant),
        retrieval_quality=quality,  # type: ignore[arg-type]
    )
