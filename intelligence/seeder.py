"""intelligence/seeder.py — Bulk import from archives into pgvector (Step 29e).

Reads JSONL archives and embeds + stores them in intel_embeddings.
Deduplication via (source_type, source_id) — idempotent, safe to re-run.
Progress logged every 500 records. Embedding is CPU-bound; ~2-5 min for 15K tweets.

CLI usage:
  python3 intelligence/seeder.py --source x_tweets
  python3 intelligence/seeder.py --source x_tweets --archive-dir /mnt/archive/x_research/
  python3 intelligence/seeder.py --source gdelt    --archive-dir /mnt/archive/gdelt/
  python3 intelligence/seeder.py --source playbook --archive-dir /mnt/archive/playbook/
  python3 intelligence/seeder.py --source discovery --archive-dir /mnt/archive/discovery/
  python3 intelligence/seeder.py --all
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Ensure repo root is on path when invoked as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence.embedder import embed_batch  # noqa: E402
from intelligence.vector_store import store_embeddings_batch  # noqa: E402

logger = logging.getLogger("intelligence.seeder")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_PROGRESS_EVERY = 500
_EMBED_BATCH = 64

_DEFAULT_DIRS: dict[str, Path] = {
    "x_tweets": Path("/mnt/archive/x_research"),
    "gdelt": Path("/mnt/archive/gdelt"),
    "playbook": Path("/mnt/archive/playbook"),
    "discovery": Path("/mnt/archive/discovery"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _parse_ts(raw: object) -> datetime | None:
    """Parse various timestamp formats into a timezone-aware datetime."""
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, OSError):
        return None


def _iter_jsonl(path: Path) -> Iterator[dict]:
    """Yield parsed JSON records from a JSONL file, skipping malformed lines."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass


def _extract_tickers_simple(text: str) -> list[str]:
    """Fast $TICKER regex — Tier 1 only (no SP500 JSON lookup needed here)."""
    import re

    pattern = re.compile(r"\$([A-Z]{1,5}(?:\.[A-Z])?)", re.ASCII)
    found = {m.group(1) for m in pattern.finditer(text.upper())}
    return sorted(found)[:10]  # cap to avoid bloat


def _flush(buffer: list[dict]) -> int:
    """Embed buffer batch and insert into DB. Returns rows inserted."""
    texts = [r["content"] for r in buffer]
    embeddings = embed_batch(texts, batch_size=_EMBED_BATCH)
    for rec, emb in zip(buffer, embeddings, strict=False):
        rec["embedding"] = emb
    return store_embeddings_batch(buffer)


def _run_source(
    records: Iterator[dict],
    source_label: str,
    total_hint: int = 0,
) -> int:
    """Process an iterator of pre-built record dicts through embed + store."""
    buffer: list[dict] = []
    total = 0
    inserted = 0
    last_progress = 0
    t0 = time.monotonic()

    for rec in records:
        if not rec.get("content", "").strip():
            continue
        buffer.append(rec)
        total += 1

        if len(buffer) >= _EMBED_BATCH:
            inserted += _flush(buffer)
            buffer = []

        if total - last_progress >= _PROGRESS_EVERY:
            elapsed = time.monotonic() - t0
            rate = total / max(elapsed, 0.001)
            logger.info("  %s progress: %d records (%.0f/s)", source_label, total, rate)
            last_progress = total

    if buffer:
        inserted += _flush(buffer)

    elapsed = time.monotonic() - t0
    logger.info(
        "✅ %s: %d records processed, %d inserted in %.1fs (%.0f/s)",
        source_label,
        total,
        inserted,
        elapsed,
        total / max(elapsed, 0.001),
    )
    return inserted


# ── Source-specific parsers ───────────────────────────────────────────────────


def _parse_x_tweet(rec: dict, harvest_file: str) -> dict | None:
    text = rec.get("text", "").strip()
    if not text:
        return None
    tweet_id = str(rec.get("id", ""))
    author = rec.get("author_username") or rec.get("author_name") or "unknown"
    tickers = _extract_tickers_simple(text)
    return {
        "content": text,
        "source_type": "x_tweet",
        "source_id": tweet_id or None,
        "source_channel": None,
        "metadata": {
            "author": author,
            "author_followers": rec.get("author_followers", 0),
            "engagement_score": rec.get("engagement_score", 0),
            "engagement_normalized": rec.get("engagement_normalized", 0.0),
            "metrics": rec.get("metrics", {}),
            "harvest_file": harvest_file,
        },
        "tickers": tickers,
        "timestamp": _parse_ts(rec.get("created_at")),
        "embedding": None,
    }


def seed_x_tweets(archive_dir: Path) -> int:
    """Embed and store all X harvester tweets from archive_dir JSONL files."""
    if not archive_dir.exists():
        logger.warning("Archive dir not found: %s — skipping x_tweets", archive_dir)
        return 0

    jsonl_files = sorted(archive_dir.glob("*.jsonl"))
    logger.info("📂 X tweets: found %d JSONL files in %s", len(jsonl_files), archive_dir)

    def _records() -> Iterator[dict]:
        for jfile in jsonl_files:
            for raw in _iter_jsonl(jfile):
                rec = _parse_x_tweet(raw, jfile.name)
                if rec:
                    yield rec

    return _run_source(_records(), "x_tweets")


def seed_gdelt(archive_dir: Path) -> int:
    """Embed and store GDELT intel from archive_dir JSONL files."""
    if not archive_dir.exists():
        logger.warning("GDELT archive not found: %s — skipping", archive_dir)
        return 0

    jsonl_files = sorted(archive_dir.glob("*.jsonl"))
    logger.info("📂 GDELT: found %d JSONL files in %s", len(jsonl_files), archive_dir)

    def _records() -> Iterator[dict]:
        for jfile in jsonl_files:
            for raw in _iter_jsonl(jfile):
                content = raw.get("title") or raw.get("content") or raw.get("text") or ""
                if isinstance(content, dict):
                    content = str(content)
                content = content.strip()
                if not content:
                    continue
                article_id = raw.get("url") or raw.get("id") or ""
                tickers = _extract_tickers_simple(content)
                yield {
                    "content": content,
                    "source_type": "gdelt_article",
                    "source_id": str(article_id)[:255] if article_id else None,
                    "source_channel": "intel:geo_risk_score",
                    "metadata": {k: v for k, v in raw.items() if k not in ("title", "content", "text")},
                    "tickers": tickers,
                    "timestamp": _parse_ts(raw.get("timestamp") or raw.get("created_at") or raw.get("date")),
                    "embedding": None,
                }

    return _run_source(_records(), "gdelt")


def seed_playbook(archive_dir: Path) -> int:
    """Embed and store playbook snapshots from archive_dir JSONL files."""
    if not archive_dir.exists():
        logger.warning("Playbook archive not found: %s — skipping", archive_dir)
        return 0

    jsonl_files = sorted(archive_dir.glob("*.jsonl"))
    logger.info("📂 Playbook: found %d JSONL files in %s", len(jsonl_files), archive_dir)

    def _records() -> Iterator[dict]:
        for jfile in jsonl_files:
            for raw in _iter_jsonl(jfile):
                summary = raw.get("summary") or raw.get("content") or ""
                if not isinstance(summary, str):
                    summary = json.dumps(summary)
                summary = summary.strip()
                if not summary:
                    continue
                snap_id = raw.get("id") or raw.get("snapshot_id") or ""
                yield {
                    "content": summary,
                    "source_type": "playbook_snapshot",
                    "source_id": str(snap_id)[:255] if snap_id else None,
                    "source_channel": "intel:playbook_snapshot",
                    "metadata": raw,
                    "tickers": [],
                    "timestamp": _parse_ts(raw.get("timestamp") or raw.get("created_at")),
                    "embedding": None,
                }

    return _run_source(_records(), "playbook")


def seed_discovery(archive_dir: Path) -> int:
    """Embed and store discovery audit log records from archive_dir JSONL files."""
    if not archive_dir.exists():
        logger.warning("Discovery archive not found: %s — skipping", archive_dir)
        return 0

    jsonl_files = sorted(archive_dir.glob("*.jsonl"))
    logger.info("📂 Discovery: found %d JSONL files in %s", len(jsonl_files), archive_dir)

    def _records() -> Iterator[dict]:
        for jfile in jsonl_files:
            for raw in _iter_jsonl(jfile):
                ticker = raw.get("ticker", "")
                action = raw.get("action", "")
                channel = raw.get("source_channel", "")
                payload = raw.get("payload")
                content = f"ticker={ticker} action={action} source={channel}"
                if payload:
                    content += f" {json.dumps(payload)[:200]}"
                content = content.strip()
                if not content or content == "ticker= action= source=":
                    continue
                rec_id = f"{ticker}_{raw.get('timestamp', '')}"
                yield {
                    "content": content,
                    "source_type": "discovery_audit",
                    "source_id": rec_id[:255],
                    "source_channel": "intel:discovery",
                    "metadata": raw,
                    "tickers": [ticker] if ticker else [],
                    "timestamp": _parse_ts(raw.get("timestamp")),
                    "embedding": None,
                }

    return _run_source(_records(), "discovery")


# ── CLI Entrypoint ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Cemini Vector DB Seeder (Step 29e)")
    parser.add_argument(
        "--source",
        choices=["x_tweets", "gdelt", "playbook", "discovery"],
        help="Which archive to seed",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        help="Override default archive directory for the chosen source",
    )
    parser.add_argument("--all", action="store_true", help="Seed all sources sequentially")
    args = parser.parse_args()

    if not args.all and not args.source:
        parser.error("Specify --source or --all")

    grand_total = 0
    t0 = time.monotonic()

    sources = ["x_tweets", "gdelt", "playbook", "discovery"] if args.all else [args.source]

    for src in sources:
        archive_dir = args.archive_dir if (not args.all and args.archive_dir) else _DEFAULT_DIRS[src]
        if src == "x_tweets":
            grand_total += seed_x_tweets(archive_dir)
        elif src == "gdelt":
            grand_total += seed_gdelt(archive_dir)
        elif src == "playbook":
            grand_total += seed_playbook(archive_dir)
        elif src == "discovery":
            grand_total += seed_discovery(archive_dir)

    elapsed = time.monotonic() - t0
    logger.info("🎉 Seeding complete: %d total records inserted in %.1fs", grand_total, elapsed)


if __name__ == "__main__":
    main()
