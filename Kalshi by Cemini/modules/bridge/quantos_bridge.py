import httpx
import asyncio

class QuantOSBridge:
    """
    Cemini Financial Suite Protocol: QuantOS Bridge.
    Enables Kalshi by Cemini to communicate with the QuantOS Engine on Port 8001.
    Set QUANTOS_HOST env var to the Docker service name (e.g. "signal_generator") in containers.
    """
    def __init__(self, host=None, port=None):
        import os
        host = host or os.getenv("QUANTOS_HOST", "127.0.0.1")
        port = port or int(os.getenv("QUANTOS_PORT", "8001"))
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)

    async def get_quantos_status(self):
        """Fetches the current status and active strategies from QuantOS."""
        try:
            # Assumes /api/status endpoint exists in QuantOS
            resp = await self.client.get("/api/status")
            return resp.json()
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    async def get_market_sentiment(self):
        """Queries QuantOS for high-level market volatility and sentiment signals."""
        try:
            resp = await self.client.get("/api/sentiment")
            return resp.json()
        except:
            return {"volatility": "NORMAL", "bias": "NEUTRAL"}

    async def trigger_quantos_hedge(self, payload: dict):
        """Requests QuantOS to execute a hedge based on Kalshi market signals."""
        try:
            resp = await self.client.post("/api/hedge", json=payload)
            return resp.json()
        except Exception as e:
            return {"status": "error", "msg": "Bridge Connection Failed", "detail": str(e)}

    async def close(self):
        await self.client.aclose()
