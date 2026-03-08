import asyncio
import logging
import os
import time
import requests
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from typing import Dict, Any
from beartype import beartype
from core.ems.base import BaseExecutionAdapter
from core.schemas.trading_signals import TradingSignal

_logger = logging.getLogger("kalshi_rest_adapter")

# D2: Fallback buying power when API is unreachable (graceful degradation).
# Position sizing through this adapter should never divide by zero.
_BUYING_POWER_FALLBACK = 1000.0

class KalshiRESTAdapter(BaseExecutionAdapter):
    """
    D14: EMS adapter wrapper around the Kalshi REST API.

    Implements BaseExecutionAdapter (get_buying_power / execute_order).
    Used by KalshiFIXAdapter as its balance-query delegate and by any
    EMS router that needs direct Kalshi REST execution.
    For the standalone raw client (used in ems/main.py signal listener),
    see ems/kalshi_rest.py → KalshiRESTv2.
    """
    def __init__(self, key_id: str, private_key_path: str, environment: str = "demo"):
        self.key_id = key_id
        self.private_key_path = private_key_path
        self.environment = environment
        self.base_url = "https://demo-api.kalshi.co/trade-api/v2" if environment == "demo" else "https://api.elections.kalshi.com/trade-api/v2"
        self.private_key = self._load_private_key()

    def _load_private_key(self):
        if not os.path.exists(self.private_key_path):
            _logger.warning("Kalshi REST: Key not found at %s", self.private_key_path)
            return None
        try:
            with open(self.private_key_path, "rb") as key_file:
                return serialization.load_pem_private_key(key_file.read(), password=None)
        except Exception as e:
            _logger.error("Kalshi REST: Key Load Error: %s", e)
            return None

    def _get_auth_headers(self, method: str, path: str, body: str = ""):
        timestamp = str(int(time.time() * 1000))
        msg = timestamp + method + path + body
        signature = self.private_key.sign(
            msg.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode(),
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

    @beartype
    async def get_buying_power(self) -> float:
        """Query live Kalshi balance. Falls back to _BUYING_POWER_FALLBACK on any error."""
        if not self.private_key:
            _logger.warning(
                "Kalshi REST: private key not loaded — returning fallback buying power $%.2f",
                _BUYING_POWER_FALLBACK,
            )
            return _BUYING_POWER_FALLBACK
        path = "/portfolio/balance"
        headers = self._get_auth_headers("GET", path)
        try:
            resp = await asyncio.to_thread(requests.get, self.base_url + path, headers=headers)
            if resp.status_code == 200:
                return float(resp.json().get("balance", 0) / 100.0)
            _logger.warning(
                "Kalshi REST: Balance endpoint returned HTTP %s — falling back to $%.2f",
                resp.status_code,
                _BUYING_POWER_FALLBACK,
            )
        except Exception as e:
            _logger.warning(
                "Kalshi REST: Balance API call failed (%s) — falling back to $%.2f",
                e,
                _BUYING_POWER_FALLBACK,
            )
        return _BUYING_POWER_FALLBACK

    @beartype
    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        if not self.private_key:
            return {"status": "error", "message": "Private key not loaded"}

        import httpx

        path = "/portfolio/orders"
        # count: 1 contract per 1% allocation (proposed_allocation_pct is 0.0–0.10)
        count = max(1, round(signal.proposed_allocation_pct * 100))
        payload = {
            "ticker": signal.ticker_or_event,
            "action": signal.action,
            "type": "market",
            "count": count,
            "side": "yes",
            "yes_price": 99,  # market-order sentinel per Kalshi API
        }
        # _get_auth_headers signs: timestamp + method + path (body="" is a no-op)
        headers = self._get_auth_headers("POST", path)
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
            if resp.status_code in [200, 201]:
                print(f"✅ Kalshi REST: Order placed — {signal.ticker_or_event} ({count} contracts)")
                return {"status": "success", "ticker": signal.ticker_or_event, "order": resp.json()}
            else:
                return {"status": "error", "code": resp.status_code, "detail": resp.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
