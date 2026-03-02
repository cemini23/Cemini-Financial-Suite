"""
ws_client.py — Authenticated Kalshi WebSocket connection manager.

Auth: RSA-PSS with SHA-256 (same scheme as REST API).
Signed message: timestamp_ms + "GET" + "/trade-api/ws/v2"
Headers:  KALSHI-ACCESS-KEY | KALSHI-ACCESS-SIGNATURE | KALSHI-ACCESS-TIMESTAMP

Endpoint: wss://api.elections.kalshi.com/trade-api/ws/v2
"""

import asyncio
import base64
import json
import logging
import os
import time
from typing import Awaitable, Callable, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

try:
    import websockets
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False

logger = logging.getLogger("kalshi.ws_client")

WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"
WS_PATH = "/trade-api/ws/v2"
BACKOFF_INITIAL = 1    # seconds
BACKOFF_MAX = 60       # seconds


# ── Auth helpers ───────────────────────────────────────────────────────────────

def load_private_key(key_path: Optional[str] = None):
    """Load RSA private key from PEM file."""
    path = key_path or os.getenv("KALSHI_PRIVATE_KEY_PATH", "private_key.pem")
    with open(path, "rb") as fh:
        return serialization.load_pem_private_key(fh.read(), password=None)


def build_auth_headers(api_key: str, private_key) -> dict:
    """
    Build RSA-PSS signed authentication headers for the WebSocket handshake.

    Kalshi requires the same signing scheme as the REST API:
      message = timestamp_ms + "GET" + "/trade-api/ws/v2"
      signature = RSA-PSS(SHA-256, MGF1, digest-length salt)
    """
    ts = str(int(time.time() * 1000))
    msg_to_sign = (ts + "GET" + WS_PATH).encode("utf-8")
    # PSS.DIGEST_LENGTH was added in cryptography 2.5; fall back to 32 (SHA-256 digest size)
    _pss_salt = getattr(padding.PSS, "DIGEST_LENGTH", 32)
    signature = private_key.sign(
        msg_to_sign,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=_pss_salt,
        ),
        hashes.SHA256(),
    )
    sig_b64 = base64.b64encode(signature).decode("utf-8")
    return {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-SIGNATURE": sig_b64,
        "KALSHI-ACCESS-TIMESTAMP": ts,
    }


# ── Client ─────────────────────────────────────────────────────────────────────

class KalshiWebSocketClient:
    """
    Long-lived authenticated WebSocket client for the Kalshi Trade API v2.

    Features:
    - RSA-PSS auth headers on every connection attempt
    - Auto-reconnect with exponential backoff (1s → 2s → 4s → ... → 60s)
    - Subscription replay on reconnect
    - Ping/pong heartbeat handled automatically by the websockets library
    - Message dispatch to a single async callback
    """

    def __init__(
        self,
        on_message: Callable[[dict], Awaitable[None]],
        api_key: Optional[str] = None,
        private_key=None,
    ):
        self._on_message = on_message
        self._api_key = api_key or os.getenv("KALSHI_API_KEY", "")
        # private_key can be injected (tests) or loaded lazily from disk (prod)
        self._private_key = private_key
        self._ws = None
        self._running = False
        self._msg_id = 0
        # Track subscriptions for replay after reconnect
        self._subscriptions: list[dict] = []

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_key(self):
        if self._private_key is not None:
            return self._private_key
        return load_private_key()

    def _build_headers(self) -> dict:
        return build_auth_headers(self._api_key, self._get_key())

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    # ── Public API ─────────────────────────────────────────────────────────────

    async def subscribe(
        self,
        channels: list,
        market_tickers: Optional[list] = None,
        send_initial_snapshot: bool = True,
    ) -> None:
        """
        Send a channel subscription request.

        Subscriptions are also queued so they are automatically replayed
        on reconnect without the caller needing to track them.
        """
        params: dict = {"channels": channels}
        if market_tickers:
            if len(market_tickers) == 1:
                params["market_ticker"] = market_tickers[0]
            else:
                params["market_tickers"] = market_tickers
        if "orderbook_delta" in channels:
            params["send_initial_snapshot"] = send_initial_snapshot

        msg = {"id": self._next_id(), "cmd": "subscribe", "params": params}
        self._subscriptions.append(msg)
        if self._ws:
            await self._ws.send(json.dumps(msg))

    async def _replay_subscriptions(self) -> None:
        """Re-send all stored subscriptions after a reconnect."""
        for sub in self._subscriptions:
            sub["id"] = self._next_id()
            await self._ws.send(json.dumps(sub))

    async def run(self, on_connected: Optional[Callable] = None) -> None:
        """
        Connect and run the receive loop with automatic reconnection.

        on_connected(client) is awaited once per successful connection.
        If on_connected is not provided, stored subscriptions are replayed.
        The caller is responsible for calling subscribe() inside on_connected.
        """
        if not _WS_AVAILABLE:
            logger.error("❌ websockets library not installed")
            return

        self._running = True
        backoff = BACKOFF_INITIAL

        while self._running:
            try:
                headers = self._build_headers()
                async with websockets.connect(
                    WS_URL,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=30,
                ) as ws:
                    self._ws = ws
                    backoff = BACKOFF_INITIAL  # reset on successful connect
                    logger.info("🔌 Kalshi WebSocket connected")

                    if on_connected:
                        await on_connected(self)
                    else:
                        await self._replay_subscriptions()

                    async for raw in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(raw)
                            await self._on_message(msg)
                        except Exception as exc:
                            logger.error("❌ Message handler error: %s", exc)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(
                    "🔄 WebSocket disconnected (%s) — retrying in %ds", exc, backoff
                )

            if self._running:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)

        self._ws = None
        logger.info("🔌 WebSocket client stopped")

    def stop(self) -> None:
        """Signal the run loop to exit after the current iteration."""
        self._running = False
