import pandas as pd
import numpy as np

class TechnicalAnalyst:
    def apply_advanced_indicators(self, df: pd.DataFrame):
        """
        Applies Institutional-Grade Indicators for 5m Scalping using pure Pandas.
        Includes VWAP, OBV, ADX, Stochastic RSI, and ATR.
        """
        if df.empty: return df

        # 1. VWAP (Volume Weighted Average Price)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        df['VWAP_D'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

        # 2. On-Balance Volume (OBV)
        df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()

        # 3. ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR_14'] = true_range.rolling(14).mean()
        df['ATR'] = df['ATR_14'] # Alias for Dynamic Risk Management

        # 4. ADX (Average Directional Index)
        up_move = df['high'] - df['high'].shift(1)
        down_move = df['low'].shift(1) - df['low']
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        tr_smooth = true_range.rolling(window=14).sum()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).sum() / tr_smooth)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).sum() / tr_smooth)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX_14'] = dx.rolling(window=14).mean()

        # 5. Stochastic RSI
        # First calculate standard RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        # Then calculate Stochastic RSI
        rsi_min = rsi.rolling(window=14).min()
        rsi_max = rsi.rolling(window=14).max()
        df['STOCHRSIk_14_14_3_3'] = 100 * (rsi - rsi_min) / (rsi_max - rsi_min)
        df['STOCHRSId_14_14_3_3'] = df['STOCHRSIk_14_14_3_3'].rolling(window=3).mean()

        # 6. EMA Ribbon
        df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Keep original RSI for dashboard compatibility
        df['RSI'] = rsi
        # Bollinger Bands for compatibility
        df['BBM_20_2.0'] = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['BBU_20_2.0'] = df['BBM_20_2.0'] + (std * 2)
        df['BBL_20_2.0'] = df['BBM_20_2.0'] - (std * 2)
        # MACD for compatibility
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_12_26_9'] = exp1 - exp2
        df['MACDs_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()

        return df
