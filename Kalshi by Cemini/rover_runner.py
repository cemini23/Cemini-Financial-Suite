"""
CEMINI FINANCIAL SUITE™ — Market Rover Runner
Standalone loop: discovers all Kalshi markets every 15 minutes,
categorises them, routes to the appropriate analyzer, and publishes
intel to the Redis Intel Bus.

Step 48: APScheduler replaces while True: asyncio.sleep() for deterministic
scheduling. Aiobreaker circuit breaker wraps scan_markets(). Async retry
via tenacity on Kalshi API transport errors.
"""
import asyncio
import os
import sys
import time

from modules.market_rover.rover import MarketRover

# ── Step 48: Resilience ───────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
try:
    from core.resilience import (
        create_circuit_breaker,
        create_async_retry_decorator,
        create_scheduler,
        add_harvester_job,
    )
    from core.resilience_metrics import record_circuit_open, record_retry

    _rover_cb = create_circuit_breaker("rover_scanner", fail_max=3, timeout_duration=120.0)
    _rover_retry = create_async_retry_decorator(
        "rover_scanner", max_attempts=3, base_wait=2.0, max_wait=30.0,
        retryable_statuses=(429, 500, 502, 503, 504),
    )
    _RESILIENCE_AVAILABLE = True
except ImportError:
    _RESILIENCE_AVAILABLE = False
    _rover_cb = None
    _rover_retry = None

SCAN_INTERVAL = 900  # 15 minutes

_rover = MarketRover()


async def _do_scan() -> dict:
    """Inner scan — wrapped by retry decorator if resilience is available."""
    return await _rover.scan_markets()


if _RESILIENCE_AVAILABLE and _rover_retry is not None:
    _scan_with_retry = _rover_retry(_do_scan)
else:
    _scan_with_retry = _do_scan


async def rover_scan_job() -> None:
    """APScheduler job: scan Kalshi markets, log results."""
    print(
        f"ROVER: Initiating market scan at "
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} UTC..."
    )
    try:
        if _RESILIENCE_AVAILABLE and _rover_cb is not None:
            results = await _rover_cb.call(_scan_with_retry)
        else:
            results = await _scan_with_retry()

        if results is None:
            print("ROVER: Scan skipped — circuit breaker OPEN")
            return

        findings = results.get("findings", [])
        counts = results.get("category_counts", {})
        unmatched = results.get("unmatched_count", 0)
        error = results.get("error")

        if error:
            print(f"ROVER: Scan returned error: {error}")
        else:
            cats_str = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
            print(
                f"ROVER: Scan complete — {len(findings)} actionable "
                f"markets [{cats_str}] | {unmatched} unmatched"
            )
    except Exception as e:
        print(f"ROVER: Scan error: {e}")


async def main() -> None:
    print("ROVER: Market Scanner starting (15-minute scan cycle, APScheduler)...")

    if _RESILIENCE_AVAILABLE:
        scheduler = create_scheduler()
        add_harvester_job(scheduler, rover_scan_job, SCAN_INTERVAL, "rover_scan")
        scheduler.start()
        print(f"ROVER: APScheduler started — next scan in up to {SCAN_INTERVAL}s")
        # Keep alive indefinitely — asyncio.Event avoids busy-sleep  # noqa: ASYNC110
        _stop_event = asyncio.Event()
        await _stop_event.wait()
    else:
        # Fallback: original while-loop pattern
        while True:
            await rover_scan_job()
            print(f"ROVER: Next scan in {SCAN_INTERVAL // 60} minutes...")
            await asyncio.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
