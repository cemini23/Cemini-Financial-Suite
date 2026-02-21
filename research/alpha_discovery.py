import polars as pl
import vectorbt as vbt
import numpy as np
import os

def run_vectorized_parameter_sweep(parquet_file: str):
    """
    Performs a massive vectorized backtest using Polars + VectorBT.
    Identifies optimal parameters for a dual Moving Average crossover strategy.
    """
    if not os.path.exists(parquet_file):
        print(f"⚠️ Data file {parquet_file} not found. Skipping sweep.")
        return None

    # 1. Load historical data instantly via Polars
    # Using scan_parquet for memory efficiency on large datasets
    lazy_df = pl.scan_parquet(parquet_file)
    df = lazy_df.collect()
    
    # 2. Extract the closing prices as a raw C-contiguous NumPy array
    close_prices = df["close"].to_numpy()
    
    # 3. Define the parameter grid
    # testing every fast MA from 10 to 50 against slow MAs from 50 to 200
    fast_windows = np.arange(10, 51)
    slow_windows = np.arange(100, 201)
    
    print(f"🚀 VectorBT: Testing {len(fast_windows) * len(slow_windows)} parameter combinations...")

    # 4. VectorBT calculates ALL combinations instantly using Numba
    # We use vbt.MA.run to generate the indicators for all windows
    ma_fast = vbt.MA.run(close_prices, window=fast_windows)
    ma_slow = vbt.MA.run(close_prices, window=slow_windows)
    
    # 5. Generate entry and exit signals for the entire grid simultaneously
    # ma_fast.ma_crossed_above(ma_slow) returns a boolean matrix
    entries = ma_fast.ma_crossed_above(ma_slow)
    exits = ma_fast.ma_crossed_below(ma_slow)
    
    # 6. Execute the vectorized backtest
    # This runs thousands of backtests in a single pass
    portfolio = vbt.Portfolio.from_signals(close_prices, entries, exits, freq='1m')
    
    # 7. Extract the winning parameters based on Total Return
    returns = portfolio.total_return()
    best_idx = returns.idxmax()
    
    # VectorBT returns a multi-index for these combinations
    # best_idx will look like (fast_window, slow_window)
    print(f"✨ OPTIMAL ALPHA FOUND:")
    print(f"   - Fast MA: {best_idx[0]}")
    print(f"   - Slow MA: {best_idx[1]}")
    print(f"   - Total Return: {returns.max():.2%}")
    
    return portfolio, best_idx

if __name__ == "__main__":
    # Example usage:
    # portfolio, best_params = run_vectorized_parameter_sweep("data/historical/btc_1m_ticks.parquet")
    pass
