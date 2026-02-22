import httpx
import asyncio
import yfinance as yf
from app.core.config import settings
import sys as _sys
import os as _os
_repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..'))
if _repo_root not in _sys.path:
    _sys.path.append(_repo_root)
from core.intel_bus import IntelPublisher, IntelReader

class PowellAnalyzer:
    """
    Module 4: The Powell Protocol (Institutional Upgrade).
    Integrates Live Treasury Yields and Intel Bus sentiment for macro-arbitrage.
    QuantOSBridge HTTP calls replaced with direct IntelReader reads (faster, Docker-native).
    """
    def __init__(self):
        self.baseline_probabilities = {
            "PAUSE": 0.70,
            "HIKE_25": 0.05,
            "CUT_25": 0.25
        }

    async def get_treasury_yields(self):
        """
        Fetches live US Treasury Yields using yfinance.
        ^IRX: 13-week T-Bill (Short-term)
        ^TNX: 10-year Treasury Note (Long-term)
        """
        try:
            # Running yfinance in a thread to keep it async-friendly
            loop = asyncio.get_event_loop()
            irx = await loop.run_in_executor(None, lambda: yf.Ticker("^IRX").fast_info['last_price'])
            tnx = await loop.run_in_executor(None, lambda: yf.Ticker("^TNX").fast_info['last_price'])

            inversion = irx - tnx # Positive = Inverted (Recession risk high)
            return {"irx": irx, "tnx": tnx, "inversion": round(inversion, 3)}
        except Exception as e:
            print(f"[!] Yield Fetch Error: {e}")
            return {"irx": 0, "tnx": 0, "inversion": 0}

    async def _read_bus_sentiment(self) -> dict:
        """
        Reads QuantOS market sentiment from the Intel Bus instead of HTTP bridge.
        Falls back to neutral signals if bus key is absent or Redis is unavailable.
        """
        vix_signal = await IntelReader.read_async("intel:vix_level")
        trend_signal = await IntelReader.read_async("intel:spy_trend")
        volatility = "HIGH" if (vix_signal and float(vix_signal["value"]) > 25) else "NORMAL"
        bias_raw = trend_signal["value"] if trend_signal else "neutral"
        bias = bias_raw.upper() if isinstance(bias_raw, str) else "NEUTRAL"
        return {"volatility": volatility, "bias": bias}

    async def analyze_fed_market(self):
        """
        Calculates Adjusted Probabilities based on Yield Curve and Intel Bus Sentiment.
        """
        # 1. Gather Macro Intelligence (bus read replaces QuantOSBridge HTTP call)
        yields_task = self.get_treasury_yields()
        bus_task = self._read_bus_sentiment()

        yields, q_sentiment = await asyncio.gather(yields_task, bus_task)

        # 2. Apply Dynamic Modifiers
        probs = self.baseline_probabilities.copy()

        # A. Yield Curve Modifier (Inversion = Recession/Cut Pressure)
        if yields['inversion'] > 0.5:
            # Strong inversion increases CUT probability
            probs["CUT_25"] += 0.15
            probs["PAUSE"] -= 0.10
            probs["HIKE_25"] -= 0.05

        # B. QuantOS Sentiment Modifier (High Volatility = Pause Pressure)
        if q_sentiment.get('volatility') == "HIGH":
            probs["PAUSE"] += 0.10
            probs["CUT_25"] += 0.05
            probs["HIKE_25"] -= 0.15

        # Ensure total prob = 1.0 (Normalization)
        total = sum(probs.values())
        probs = {k: round(v/total, 2) for k, v in probs.items()}

        # Intel Bus: publish fed bias so QuantOS and other Kalshi modules can read it
        _dominant = max(probs, key=probs.get)
        _fed_bias = "dovish" if _dominant == "CUT_25" else "hawkish" if _dominant == "HIKE_25" else "neutral"
        await IntelPublisher.publish_async(
            "intel:fed_bias",
            {"bias": _fed_bias, "confidence": probs[_dominant]},
            source_system="PowellAnalyzer",
            confidence=probs[_dominant]
        )

        # 3. Compare with Live Kalshi Market Prices
        _no_signal_base = {
            "macro_indicators": {
                "yield_curve": "NORMAL" if yields['inversion'] <= 0 else "INVERTED",
                "spread_13w_10y": yields['inversion'],
                "quantos_sentiment": q_sentiment.get('bias', 'NEUTRAL')
            },
            "adjusted_consensus": probs,
            "opportunities": [],
        }
        try:
            async with httpx.AsyncClient() as client:
                m_res = await client.get(
                    "https://api.elections.kalshi.com/trade-api/v2/markets",
                    params={"series_ticker": "KXFED", "status": "open"},
                    timeout=5.0
                )
            if m_res.status_code != 200:
                raise ValueError(f"HTTP {m_res.status_code}")
            fed_markets = m_res.json().get('markets', [])
        except Exception as e:
            print(f"[WARNING] Powell Protocol: Kalshi API failed ({e}). Returning NO_SIGNAL — no trade signal.")
            return {**_no_signal_base, "status": "no_signal", "msg": f"Kalshi API failed: {e}"}

        if not fed_markets:
            print("[WARNING] Powell Protocol: No active KXFED markets on Kalshi. Returning NO_SIGNAL.")
            return {**_no_signal_base, "status": "no_signal", "msg": "No active KXFED markets"}

        kalshi_market = {}
        for m in fed_markets:
            title = (m.get('subtitle') or m.get('title', '')).upper()
            yes_bid = m.get('yes_bid', 0) / 100.0
            if any(w in title for w in ['PAUSE', 'HOLD', 'UNCHANGED', 'NO CHANGE']):
                kalshi_market['PAUSE'] = yes_bid
            elif any(w in title for w in ['HIKE', 'RAISE', 'INCREASE', '+25']):
                kalshi_market['HIKE_25'] = yes_bid
            elif any(w in title for w in ['CUT', 'LOWER', 'DECREASE', 'REDUCTION', '-25']):
                kalshi_market['CUT_25'] = yes_bid

        if not kalshi_market:
            print("[WARNING] Powell Protocol: Could not map KXFED markets to rate outcomes. Returning NO_SIGNAL.")
            return {**_no_signal_base, "status": "no_signal", "msg": "Could not map market outcomes"}

        opportunities = []

        for bracket, prob in probs.items():
            market_price = kalshi_market.get(bracket, 0)
            if prob > (market_price + 0.10):
                opportunities.append({
                    "bracket": bracket,
                    "model_prob": f"{prob*100}%",
                    "kalshi_price": f"${market_price:.2f}",
                    "signal": "MACRO ALPHA",
                    "expected_value": round((1.0 / market_price) * prob, 2)
                })

        return {
            "macro_indicators": {
                "yield_curve": "INVERTED" if yields['inversion'] > 0 else "NORMAL",
                "spread_13w_10y": yields['inversion'],
                "quantos_sentiment": q_sentiment.get('bias', 'NEUTRAL')
            },
            "adjusted_consensus": probs,
            "opportunities": opportunities,
            "status": "LIVE_SYNC"
        }
