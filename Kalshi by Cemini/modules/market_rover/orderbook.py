"""
orderbook.py — Local order book reconstruction from the Kalshi WebSocket stream.

Protocol:
  1. Subscribe to orderbook_delta with send_initial_snapshot=True
  2. Receive orderbook_snapshot → initialise local book in Redis sorted sets
  3. Receive orderbook_delta messages → apply sequentially, tracking seq numbers
  4. If seq gap is detected → return False so caller can re-subscribe

Redis layout:
  kalshi:ob:{ticker}:yes    sorted set   score=price_cents  member="qty@price"
  kalshi:ob:{ticker}:no     sorted set   score=price_cents  member="qty@price"
  kalshi:ob:{ticker}:bbo    hash         best_bid, best_ask, spread, updated_at
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("kalshi.orderbook")


def _yes_key(ticker: str) -> str:
    return f"kalshi:ob:{ticker}:yes"


def _no_key(ticker: str) -> str:
    return f"kalshi:ob:{ticker}:no"


def _bbo_key(ticker: str) -> str:
    return f"kalshi:ob:{ticker}:bbo"


class OrderBookManager:
    """
    Maintains a local mirror of Kalshi order books in Redis sorted sets.

    Each price level is stored as:
        ZADD kalshi:ob:{ticker}:{side}  SCORE=price_cents  MEMBER="qty@price"

    For example, [price=45, qty=100] on the yes side becomes:
        ZADD kalshi:ob:BTCX-24:yes  45  "100@45"

    To update a level on delta:
        1. ZRANGEBYSCORE to find the existing "?@{price}" member
        2. ZREM the old member
        3. ZADD the new member with updated qty (or skip if qty <= 0)
    """

    def __init__(self, redis_client):
        self._r = redis_client
        # Per-ticker expected next seq; None = no snapshot received yet
        self._expected_seq: dict[str, Optional[int]] = {}

    # ── Snapshot ───────────────────────────────────────────────────────────────

    async def apply_snapshot(self, msg: dict) -> None:
        """
        Process an orderbook_snapshot WebSocket message.
        Clears the existing Redis book for this ticker and repopulates it.
        """
        inner = msg.get("msg", {})
        ticker = inner.get("market_ticker", "")
        seq = msg.get("seq", 0)
        yes_levels = inner.get("yes", [])  # [[price_cents, qty], ...]
        no_levels = inner.get("no", [])

        yes_k = _yes_key(ticker)
        no_k = _no_key(ticker)

        # Wipe old book
        await self._r.delete(yes_k)
        await self._r.delete(no_k)

        # Populate yes side: mapping = {member: score}
        if yes_levels:
            yes_mapping = {
                f"{qty}@{price}": float(price)
                for price, qty in yes_levels
                if qty > 0
            }
            if yes_mapping:
                await self._r.zadd(yes_k, yes_mapping)

        # Populate no side
        if no_levels:
            no_mapping = {
                f"{qty}@{price}": float(price)
                for price, qty in no_levels
                if qty > 0
            }
            if no_mapping:
                await self._r.zadd(no_k, no_mapping)

        # Next expected delta seq = snapshot_seq + 1
        self._expected_seq[ticker] = seq + 1
        await self._update_bbo(ticker)

        logger.debug(
            "📖 Snapshot %s: %d yes + %d no levels (seq=%d)",
            ticker, len(yes_levels), len(no_levels), seq,
        )

    # ── Delta ──────────────────────────────────────────────────────────────────

    async def apply_delta(self, msg: dict) -> bool:
        """
        Process an orderbook_delta WebSocket message.

        Returns:
            True  — delta applied successfully
            False — sequence gap detected; caller must re-subscribe for a fresh snapshot
        """
        inner = msg.get("msg", {})
        ticker = inner.get("market_ticker", "")
        seq = msg.get("seq")
        price = int(inner.get("price", 0))
        delta = int(inner.get("delta", 0))
        side = inner.get("side", "yes")

        # ── Sequence integrity check ──────────────────────────────────────────
        expected = self._expected_seq.get(ticker)
        if expected is not None and seq != expected:
            logger.warning(
                "⚠️  Seq gap on %s: expected=%d got=%d — re-snapshot needed",
                ticker, expected, seq,
            )
            # Discard stale expected so next snapshot can reinitialise
            self._expected_seq.pop(ticker, None)
            return False

        # ── Apply the delta to the sorted set ────────────────────────────────
        book_key = _yes_key(ticker) if side == "yes" else _no_key(ticker)

        # Find the existing qty at this price level (if any)
        existing = await self._r.zrangebyscore(book_key, price, price)
        if existing:
            old_member = existing[0]
            try:
                old_qty = int(old_member.split("@")[0])
            except (ValueError, IndexError):
                old_qty = 0
            await self._r.zrem(book_key, old_member)
        else:
            old_qty = 0

        new_qty = old_qty + delta
        if new_qty > 0:
            await self._r.zadd(book_key, {f"{new_qty}@{price}": float(price)})

        # Advance expected seq
        if expected is not None:
            self._expected_seq[ticker] = expected + 1

        await self._update_bbo(ticker)
        return True

    # ── Depth query ────────────────────────────────────────────────────────────

    async def get_total_depth(self, ticker: str, side: str = "yes") -> int:
        """Return the total number of contracts across all price levels on one side."""
        book_key = _yes_key(ticker) if side == "yes" else _no_key(ticker)
        members = await self._r.zrange(book_key, 0, -1)
        total = 0
        for member in members:
            try:
                total += int(member.split("@")[0])
            except (ValueError, IndexError):
                pass
        return total

    # ── BBO cache ──────────────────────────────────────────────────────────────

    async def _update_bbo(self, ticker: str) -> None:
        """Recompute best bid / best ask and persist to Redis hash."""
        # Best bid = highest YES price level
        yes_top = await self._r.zrevrange(_yes_key(ticker), 0, 0, withscores=True)
        # Best ask = 100 - highest NO price level (prediction market convention)
        no_top = await self._r.zrevrange(_no_key(ticker), 0, 0, withscores=True)

        best_bid = int(yes_top[0][1]) if yes_top else None
        best_ask = (100 - int(no_top[0][1])) if no_top else None
        spread = (
            (best_ask - best_bid)
            if (best_bid is not None and best_ask is not None)
            else None
        )

        bbo = {
            "best_bid":   str(best_bid) if best_bid is not None else "",
            "best_ask":   str(best_ask) if best_ask is not None else "",
            "spread":     str(spread) if spread is not None else "",
            "updated_at": str(time.time()),
        }
        await self._r.hset(_bbo_key(ticker), mapping=bbo)
