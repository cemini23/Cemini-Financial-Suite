import asyncio
import sys
import os

# Add Kalshi path to sys.path
sys.path.append(os.path.abspath("../Kalshi by Cemini"))

async def run_diag():
    from modules.weather_alpha.analyzer import WeatherAnalyzer
    print("🌤️ Starting Weather Alpha Diagnostic (Remote Exec)...")
    analyzer = WeatherAnalyzer()
    results = await analyzer.analyze_market("NYC")
    print("\n--- DIAGNOSTIC RESULTS ---")
    print(f"Status: {results.get('status')}")
    print(f"Analysis: {results.get('analysis')}")
    print(f"Opportunities: {results.get('opportunities')}")
    print(f"Confidence: {results.get('confidence_score')}")

if __name__ == "__main__":
    asyncio.run(run_diag())
