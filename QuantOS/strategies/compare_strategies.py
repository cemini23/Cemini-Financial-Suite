
import pandas as pd
from strategies.backtester import BacktestEngine
import os

def run_comparison(symbol):
    file_path = f'data/{symbol.lower()}_history.csv'
    if not os.path.exists(file_path):
        return

    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    
    # Simulating Strategy A (Current RSI)
    engine_rsi = BacktestEngine(10000)
    res_rsi = engine_rsi.run(symbol.upper(), df)
    
    print(f'\n📊 --- STRATEGY COMPARISON: {symbol.upper()} ---')
    print(f'Strategy 1 (RSI 30/70):  ROI: {res_rsi["roi"]} | Trades: {res_rsi["trades"]}')
    print(f'Strategy 2 (Trend-Mod):  [Pending Optimization]')
    print('-' * 50)

if __name__ == '__main__':
    run_comparison('SPY')
