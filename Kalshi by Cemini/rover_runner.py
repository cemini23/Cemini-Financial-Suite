"""
CEMINI FINANCIAL SUITE™ — Market Rover Runner
Standalone loop: discovers all Kalshi markets every 15 minutes,
categorises them, routes to the appropriate analyzer, and publishes
intel to the Redis Intel Bus.
"""
import asyncio
import time

from modules.market_rover.rover import MarketRover

SCAN_INTERVAL = 900  # 15 minutes


async def main():
    rover = MarketRover()
    print("ROVER: Market Scanner starting (15-minute scan cycle)...")

    while True:
        try:
            print(
                f"ROVER: Initiating market scan at "
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} UTC..."
            )
            results = await rover.scan_markets()

            findings = results.get("findings", [])
            counts = results.get("category_counts", {})
            unmatched = results.get("unmatched_count", 0)
            error = results.get("error")

            if error:
                print(f"ROVER: Scan returned error: {error}")
            else:
                cats_str = ", ".join(
                    f"{k}:{v}" for k, v in sorted(counts.items())
                )
                print(
                    f"ROVER: Scan complete — {len(findings)} actionable "
                    f"markets [{cats_str}] | {unmatched} unmatched"
                )
        except Exception as e:
            print(f"ROVER: Scan error: {e}")

        print(f"ROVER: Next scan in {SCAN_INTERVAL // 60} minutes...")
        await asyncio.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
