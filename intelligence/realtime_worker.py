"""intelligence/realtime_worker.py — Real-time embedding pipeline (Step 29f).

Subscribes to all intel:* channels via Redis psubscribe.
Buffers incoming messages and embeds in batches every VECTOR_REALTIME_FLUSH_SECONDS.
Batch size ceiling: VECTOR_REALTIME_BUFFER_SIZE (default 32).

Run standalone:
  python3 intelligence/realtime_worker.py

Or instantiate EmbeddingWorker and call run() as a background task from
opportunity_screener's lifespan handler:
  worker = EmbeddingWorker()
  asyncio.create_task(worker.run())
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Ensure repo root on path when invoked as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence.config import (  # noqa: E402
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    VECTOR_REALTIME_BUFFER_SIZE,
    VECTOR_REALTIME_FLUSH_SECONDS,
)

logger = logging.getLogger("intelligence.realtime_worker")


class EmbeddingWorker:
    """Async worker: psubscribe intel:* → buffer → batch embed → pgvector store."""

    def __init__(self) -> None:
        self._buffer: list[dict] = []
        self._running = False
        self._total_stored = 0

    async def run(self) -> None:
        """Main loop. Runs until stop() is called or the process exits."""
        import redis

        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
        pubsub = r.pubsub()
        pubsub.psubscribe("intel:*")

        self._running = True
        last_flush = time.monotonic()
        logger.info("🔌 EmbeddingWorker: subscribed to intel:* channels")

        while self._running:
            # Non-blocking poll — timeout=1.0 yields to other coroutines
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("type") == "pmessage":
                self._handle_message(msg)

            now = time.monotonic()
            if self._buffer and (
                len(self._buffer) >= VECTOR_REALTIME_BUFFER_SIZE
                or now - last_flush >= VECTOR_REALTIME_FLUSH_SECONDS
            ):
                await self._flush()
                last_flush = now

            await asyncio.sleep(0.05)  # yield to event loop

        # Final flush on shutdown
        if self._buffer:
            await self._flush()

        pubsub.close()
        logger.info("EmbeddingWorker stopped. Total stored: %d", self._total_stored)

    def _handle_message(self, msg: dict) -> None:
        channel = msg.get("channel", "")
        data = msg.get("data", "")
        try:
            payload = json.loads(data) if isinstance(data, str) else data
            if isinstance(payload, dict):
                value = payload.get("value", "")
                content = value if isinstance(value, str) else json.dumps(value)
            else:
                content = str(payload)

            content = content.strip()
            if len(content) < 5:
                return

            self._buffer.append({
                "content": content,
                "source_type": "intel_message",
                "source_id": None,
                "source_channel": channel,
                "metadata": {"source_system": payload.get("source_system", "") if isinstance(payload, dict) else ""},
                "tickers": [],
                "timestamp": None,
                "embedding": None,
            })
        except Exception as exc:
            logger.debug("EmbeddingWorker: could not parse message on %s: %s", channel, exc)

    async def _flush(self) -> None:
        if not self._buffer:
            return

        from intelligence.embedder import embed_batch
        from intelligence.vector_store import store_embeddings_batch

        batch = self._buffer[:]
        self._buffer.clear()
        try:
            texts = [r["content"] for r in batch]
            embeddings = await asyncio.get_event_loop().run_in_executor(None, embed_batch, texts)
            for rec, emb in zip(batch, embeddings, strict=False):
                rec["embedding"] = emb
            n = store_embeddings_batch(batch)
            self._total_stored += n
            logger.info("💾 EmbeddingWorker: stored %d intel embeddings (total=%d)", n, self._total_stored)
        except Exception as exc:
            logger.warning("EmbeddingWorker flush error: %s", exc)

    def stop(self) -> None:
        """Signal the run loop to exit after the current iteration."""
        self._running = False


# ── Standalone entrypoint ─────────────────────────────────────────────────────


async def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    worker = EmbeddingWorker()
    loop = asyncio.get_event_loop()

    import signal

    def _shutdown(*_):
        logger.info("Shutdown signal received")
        worker.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    await worker.run()


if __name__ == "__main__":
    asyncio.run(_main())
