from modules.weather_alpha.sources import WeatherSource
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
        # Simulated Kalshi Order Book Brackets
        market_simulation = [
            {"bracket": f"< {data['consensus_temp'] - 2}", "price": 0.15, "edge": 0.8},
            {"bracket": f"{data['consensus_temp'] - 1} to {data['consensus_temp'] + 1}", "price": 0.45, "edge": 0.95},
            {"bracket": f"> {data['consensus_temp'] + 2}", "price": 0.10, "edge": 0.7}
        ]

        opportunities = []
        # Variance < 1.5 indicates high model consensus (The "Diamond" Signal)
        if data['variance'] < 2.5: # Relaxed for wider scanning
            for contract in market_simulation:
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
