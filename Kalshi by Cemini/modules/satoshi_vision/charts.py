import ccxt.async_support as ccxt
import pandas as pd
import asyncio

class ChartReader:
    def __init__(self):
        # We use Kraken for reliable BTC/USD data
        self.exchange = ccxt.kraken()

    async def get_candles(self, asset="BTC/USD", timeframe='5m', limit=100):
        """
        Universal Candle Fetcher.
        Supported Timeframes: '5m', '15m', '1h', '4h', '1d', '1w'
        """
        try:
            # Kraken supports all standard timeframes
            # For Yearly analysis, we use weekly data
            actual_tf = '1w' if timeframe == '1y' else timeframe
            
            # Fetch OHLCV asynchronously
            ohlcv = await self.exchange.fetch_ohlcv(asset, actual_tf, limit=limit)
            
            # Convert to Pandas DataFrame for analysis
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            print(f"[!] Error fetching {timeframe} charts for {asset}: {e}")
            return pd.DataFrame()

    async def get_trend_confirmation(self):
        """
        Checks the 1h timeframe to see if we are in a macro bull or bear market.
        """
        df = await self.get_candles(asset='BTC/USD', timeframe='1h', limit=50)
        if df.empty: return "UNKNOWN"
        
        # Simple trend: Current Price vs 20 SMA
        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        return "BULLISH" if current_price > sma_20 else "BEARISH"

    async def close(self):
        await self.exchange.close()
