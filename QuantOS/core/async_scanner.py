import asyncio
import aiohttp
import time
import os
import pandas as pd
from datetime import datetime
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

class AsyncScanner:
    def __init__(self, tickers):
        self.tickers = tickers
        self.results = {}
        # Alpaca Authentication
        self.api_key = os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_SECRET_KEY")
        
        if self.api_key and "your_" not in self.api_key.lower():
            self.alpaca_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        else:
            self.alpaca_client = None

    async def fetch_alpaca_prices(self):
        """Uses Alpaca's official SDK for highly reliable batch price fetching."""
        if not self.alpaca_client:
            return {}
        
        try:
            # Fetch latest trade for all tickers in one go (up to 200)
            request_params = StockLatestTradeRequest(symbol_or_symbols=self.tickers[:200])
            latest_trades = self.alpaca_client.get_stock_latest_trade(request_params)
            
            prices = {}
            for symbol, trade in latest_trades.items():
                prices[symbol] = float(trade.price)
            return prices
        except Exception as e:
            print(f"⚠️ Alpaca Scanner Error: {e}")
            return {}

    async def fetch_yahoo_ticker(self, session, ticker):
        """Yahoo fallback for tickers not in Alpaca or if Alpaca fails."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('chart', {}).get('result', [])
                    if result:
                        return ticker, result[0]['meta']['regularMarketPrice']
        except aiohttp.ClientError as e:
            # logger.debug(f"Yahoo fetch error for {ticker}: {e}") # Too noisy for main log
            pass
        except Exception:
            pass
        return ticker, None

    async def scan_market(self):
        """Primary: Alpaca API | Secondary: Yahoo Async Bursts."""
        start_time = time.time()
        
        # 1. Try Alpaca First (Fast & Reliable)
        market_data = await self.fetch_alpaca_prices()
        
        # 2. Fill gaps with Yahoo if needed
        missing = [t for t in self.tickers if t not in market_data]
        if missing and len(market_data) < len(self.tickers):
            print(f"📡 Filling {len(missing)} gaps via Yahoo...")
            async with aiohttp.ClientSession() as session:
                burst_size = 10
                for i in range(0, len(missing), burst_size):
                    chunk = missing[i:i+burst_size]
                    tasks = [self.fetch_yahoo_ticker(session, t) for t in chunk]
                    responses = await asyncio.gather(*tasks)
                    for t, p in responses:
                        if p: market_data[t] = p
                    await asyncio.sleep(0.5)

        duration = time.time() - start_time
        print(f"⚡ SCAN COMPLETE: Gathered {len(market_data)} prices in {duration:.2f}s")
        return market_data

def run_async_scan(tickers):
    scanner = AsyncScanner(tickers)
    return asyncio.run(scanner.scan_market())
