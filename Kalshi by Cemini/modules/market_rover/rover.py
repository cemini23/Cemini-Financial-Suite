import httpx
import asyncio
import time
import sys as _sys
import os as _os
from app.core.config import settings
_repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..'))
if _repo_root not in _sys.path:
    _sys.path.append(_repo_root)
from core.intel_bus import IntelReader

# Map series ticker prefixes → category
# Weather markets (KXHIGH*) are noted but deferred to weather_alpha, which
# does its own live Kalshi query with model-consensus temperature data.
CATEGORY_MAP = [
    # Weather
    ("KXHIGH", "weather"), ("KXLOW", "weather"), ("KXRAIN", "weather"), ("KXSNOW", "weather"),
    # Crypto
    ("BTC", "crypto"), ("ETH", "crypto"), ("DOGE", "crypto"), ("SOL", "crypto"),
    ("XRP", "crypto"), ("ADA", "crypto"), ("AVAX", "crypto"),
    # Economics / macro
    ("INX", "economics"), ("SPX", "economics"), ("NDX", "economics"),
    ("FED", "economics"), ("FOMC", "economics"), ("CPI", "economics"),
    ("GDP", "economics"), ("JOBS", "economics"), ("UNEMP", "economics"),
    ("INFL", "economics"), ("PCE", "economics"), ("PPI", "economics"),
    # Politics
    ("PRES", "politics"), ("CONG", "politics"), ("SENATE", "politics"),
    ("HOUSE", "politics"), ("GOV", "politics"), ("ELEC", "politics"),
    # Sports
    ("NFL", "sports"), ("NBA", "sports"), ("MLB", "sports"), ("NHL", "sports"),
    ("NCAAF", "sports"), ("NCAAB", "sports"), ("UFC", "sports"), ("PGA", "sports"),
    ("FIFA", "sports"), ("SOCCER", "sports"),
]

# Which in-system analyzer handles each category
CATEGORY_ANALYZER = {
    "weather":     "weather_alpha",     # handled separately; rover notes only
    "crypto":      "satoshi_vision",
    "economics":   "powell_protocol",
    "politics":    "geo_pulse",
    "sports":      "UNMATCHED",
}

# Minimum cumulative volume for a market to be considered active/liquid
MIN_VOLUME = 100


class MarketRover:
    """
    Module 7: Market Rover.
    Dynamically discovers ALL active Kalshi markets via paginated API, categorises
    them, routes to the appropriate in-system analyzer, and logs unmatched markets
    for future development.
    Weather markets are noted but NOT double-signalled — weather_alpha owns them.
    """

    def __init__(self):
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"

    def _categorize(self, series_ticker: str, title: str) -> str:
        series_upper = (series_ticker or "").upper()
        for prefix, category in CATEGORY_MAP:
            if series_upper.startswith(prefix):
                return category
        # Keyword fallback on title
        t = (title or "").lower()
        if any(w in t for w in ["bitcoin", "ethereum", "crypto", "btc", "eth"]):
            return "crypto"
        if any(w in t for w in ["federal reserve", "fed rate", "cpi", "inflation", "gdp", "unemployment", "s&p"]):
            return "economics"
        if any(w in t for w in ["president", "election", "congress", "senate", "vote", "ballot", "governor"]):
            return "politics"
        if any(w in t for w in ["temperature", "rain", "snow", "hurricane", "weather", "high temp"]):
            return "weather"
        if any(w in t for w in ["nfl", "nba", "mlb", "nhl", "soccer", "championship", "super bowl", "world series"]):
            return "sports"
        return "unmatched"

    async def _fetch_all_markets(self, client: httpx.AsyncClient) -> list:
        """Paginate through all open Kalshi markets. Returns [] on any failure — no fake fallback."""
        markets = []
        cursor = None
        max_pages = 15  # 15 × 200 = up to 3,000 markets

        for page in range(max_pages):
            params = {"status": "open", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            try:
                resp = await client.get(
                    f"{self.base_url}/markets", params=params, timeout=10.0
                )
                if resp.status_code != 200:
                    print(f"API_FAIL: Kalshi /markets returned HTTP {resp.status_code}, skipping signal")
                    return []
                data = resp.json()
                page_markets = data.get("markets", [])
                if not page_markets:
                    break
                markets.extend(page_markets)
                cursor = data.get("cursor")
                if not cursor:
                    break
            except Exception as e:
                print(f"API_FAIL: Kalshi /markets fetch error ({e}), skipping signal")
                return []

        return markets

    async def scan_markets(self):
        try:
            # 1. Read QuantOS context from Intel Bus
            _vix = await IntelReader.read_async("intel:vix_level")
            _trend = await IntelReader.read_async("intel:spy_trend")
            _bias_raw = _trend["value"] if _trend else "neutral"
            q_sentiment = {
                "volatility": "HIGH" if (_vix and float(_vix["value"]) > 25) else "NORMAL",
                "bias":       _bias_raw.upper() if isinstance(_bias_raw, str) else "NEUTRAL",
                "confidence": _trend.get("confidence", 0) if _trend else 0,
            }

            # 2. Fetch all open markets — real data only
            async with httpx.AsyncClient() as client:
                all_markets = await self._fetch_all_markets(client)

            if not all_markets:
                print("API_FAIL: Kalshi returned no active markets, skipping signal")
                return {
                    "module": "MARKET-ROVER",
                    "findings": [],
                    "macro_context": q_sentiment,
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                }

            # 3. Categorise, filter by volume, build findings
            category_counts: dict = {}
            rover_findings = []
            unmatched = []

            for m in all_markets:
                ticker = m.get("ticker", "")
                series_ticker = m.get("series_ticker", "")
                title = m.get("title", "")
                volume = m.get("volume", 0) or 0

                if volume < MIN_VOLUME:
                    continue

                category = self._categorize(series_ticker, title)
                category_counts[category] = category_counts.get(category, 0) + 1

                if category == "unmatched":
                    unmatched.append({"ticker": ticker, "title": title})
                    continue

                analyzer = CATEGORY_ANALYZER.get(category, "UNMATCHED")

                # Signal: weather deferred to weather_alpha, politics to geo_pulse
                signal = "NO_SIGNAL"
                bias = q_sentiment.get("bias", "NEUTRAL")
                tl = title.lower()

                if category == "economics":
                    if bias == "BULLISH" and any(w in tl for w in ["above", "pause", "cut", "lower"]):
                        signal = "CONVERGENCE_BUY"
                    elif bias == "BEARISH" and any(w in tl for w in ["below", "hike", "raise", "higher"]):
                        signal = "CONVERGENCE_SELL"
                elif category == "crypto":
                    if bias == "BULLISH" and "above" in tl:
                        signal = "CONVERGENCE_BUY"
                    elif bias == "BEARISH" and "below" in tl:
                        signal = "CONVERGENCE_SELL"
                elif category in ("weather", "politics"):
                    signal = f"DEFER_TO_{analyzer.upper()}"

                rover_findings.append({
                    "ticker":        ticker,
                    "series_ticker": series_ticker,
                    "title":         title,
                    "category":      category,
                    "analyzer":      analyzer,
                    "volume":        volume,
                    "quantos_bias":  bias,
                    "signal":        signal,
                    "confidence":    q_sentiment.get("confidence", 0),
                })

            # 4. Log discovery summary
            cats_str = ", ".join(
                f"{k}:{v}" for k, v in sorted(category_counts.items())
            )
            print(f"ROVER: Found {len(all_markets)} active markets across [{cats_str}]")
            if unmatched:
                sample = [u["ticker"] for u in unmatched[:5]]
                tail = "..." if len(unmatched) > 5 else ""
                print(f"ROVER: UNMATCHED {len(unmatched)} markets (no analyzer assigned): {sample}{tail}")

            return {
                "module":          "MARKET-ROVER",
                "findings":        rover_findings,
                "macro_context":   q_sentiment,
                "category_counts": category_counts,
                "unmatched_count": len(unmatched),
                "timestamp":       time.strftime('%Y-%m-%d %H:%M:%S'),
            }

        except Exception as e:
            return {"module": "MARKET-ROVER", "error": str(e), "findings": []}
