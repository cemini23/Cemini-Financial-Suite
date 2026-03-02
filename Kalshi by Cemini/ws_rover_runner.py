"""
ws_rover_runner.py — Docker entrypoint for the Kalshi WebSocket rover.

Replaces rover_runner.py (15-minute REST polling) with a single persistent
WebSocket connection for real-time order book and trade data.
"""

import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ws_rover_runner")

# Ensure "Kalshi by Cemini/" directory is on sys.path (same as rover_runner.py)
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from modules.market_rover.ws_rover import WebSocketRover


async def main() -> None:
    rover = WebSocketRover()
    await rover.start()


if __name__ == "__main__":
    logger.info("WS_ROVER: Kalshi WebSocket Rover starting...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WS_ROVER: Stopped.")
