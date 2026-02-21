from modules.weather_alpha.sources import WeatherSource
import httpx
import time

class WeatherAnalyzer:
    def __init__(self):
        self.source = WeatherSource()

    async def analyze_market(self, city_code: str):
        # ... (Existing logic) ...
        # Await the high-speed async data fetch
        data = await self.source.get_aggregated_forecast(city_code)

        if not data:
            return {"status": "error", "msg": "Data Source Failure", "city": city_code}

        # --- INSTITUTIONAL ARBITRAGE LOGIC (The Math) ---
        # Fetch live Kalshi market prices for this city
        series_id = f"KXHIGH{city_code}"
        try:
            async with httpx.AsyncClient() as client:
                m_res = await client.get(
                    "https://api.elections.kalshi.com/trade-api/v2/markets",
                    params={"series_ticker": series_id, "status": "open"},
                    timeout=5.0
                )
            if m_res.status_code != 200:
                raise ValueError(f"HTTP {m_res.status_code}")
            markets = m_res.json().get('markets', [])
        except Exception as e:
            print(f"[WARNING] Weather Alpha: Kalshi API failed for {series_id} ({e}). Returning NO_SIGNAL — no trade signal.")
            return {"opportunities": [], "status": "no_signal", "msg": f"Kalshi API failed: {e}", "city": city_code}

        if not markets:
            print(f"[WARNING] Weather Alpha: No active Kalshi markets for {series_id}. Returning NO_SIGNAL.")
            return {"opportunities": [], "status": "no_signal", "msg": f"No active markets for {series_id}", "city": city_code}

        # Edge scales with model variance (lower variance = higher confidence = higher edge)
        model_edge = 0.95 if data['variance'] < 1.5 else 0.85 if data['variance'] < 2.5 else 0.70
        live_market = [
            {
                "bracket": m.get('subtitle') or m.get('title', 'Unknown'),
                "price": m.get('yes_bid', 0) / 100.0,
                "edge": model_edge
            }
            for m in markets
        ]

        opportunities = []
        # Variance < 1.5 indicates high model consensus (The "Diamond" Signal)
        if data['variance'] < 2.5: # Relaxed for wider scanning
            for contract in live_market:
                # If price is < 0.30 but models agree on this bracket -> ARBITRAGE
                if contract['price'] < 0.30:
                    opportunities.append({
                        "city": city_code,
                        "bracket": contract['bracket'],
                        "signal": "DIAMOND ALPHA" if data['variance'] < 1.5 else "GOLD ALPHA",
                        "expected_value": round((1.0 / contract['price']) * contract['edge'], 2),
                        "edge": contract['edge'],
                        "reason": f"Model variance {data['variance']} is low. Consensus is {data['consensus_temp']}°."
                    })

        return {
            "analysis": data,
            "opportunities": opportunities,
            "status": "active",
            "confidence_score": "High" if data['variance'] < 1.5 else "Moderate"
        }

    async def scan_full_us(self):
        """
        Scans all supported cities in parallel.
        Returns the best opportunity and raw data for all cities.
        """
        import asyncio
        tasks = [self.analyze_market(code) for code in self.source.cities.keys()]
        results = await asyncio.gather(*tasks)

        all_opps = []
        all_data = []
        for r in results:
            all_data.append(r)
            if r.get("opportunities"):
                all_opps.extend(r["opportunities"])

        # Sort by expected value
        all_opps = sorted(all_opps, key=lambda x: x.get('expected_value', 0), reverse=True)

        return {
            "best_opportunity": all_opps[0] if all_opps else None,
            "all_opportunities": all_opps,
            "raw_results": all_data,
            "cities_scanned": list(self.source.cities.keys()),
            "timestamp": time.time()
        }
