"""
QuantOS™ v7.0.0 - Robust Backtest Engine
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import pandas as pd
import numpy as np
import os
from config.settings_manager import settings_manager
from core.logger_config import get_logger
from strategies.analysis import calculate_confidence_score

logger = get_logger("backtester")

class BacktestEngine:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    def simulate_performance(self, start_year, end_year):
        """
        Historical Replay: Simulated Year-by-Year PnL based on actual strategy logic.
        """
        # Data Integrity Check
        spy_path = os.path.join(self.data_dir, "spy_history.csv")
        if not os.path.exists(spy_path):
            raise ValueError(f"CRITICAL: No historical data file found. Please run Harvester first.")
        
        try:
            df = pd.read_csv(spy_path)
            # FIX: Calculate Indicators if missing
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            
            if 'RSI' not in df.columns:
                logger.info("⚙️ Calculating missing RSI for simulation...")
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
            if 'SMA_200' not in df.columns:
                logger.info("⚙️ Calculating missing SMA_200 for simulation...")
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            if 'SMA_50' not in df.columns:
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                
            df.fillna(0, inplace=True)
            
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
            
            if df.empty:
                raise ValueError("Data file exists but is empty.")
            
            available_years = df.index.year.unique()
            if start_year not in available_years:
                raise ValueError(f"CRITICAL: No data found for {start_year}. Run Harvester first.")
                
        except Exception as e:
            if isinstance(e, ValueError): raise e
            raise ValueError(f"CRITICAL: Failed to read data file: {e}")

        # Fetch dynamic settings
        stop_loss = settings_manager.get("stop_loss_pct")
        take_profit = settings_manager.get("take_profit_pct")
        min_threshold = settings_manager.get("backtest_min_score") or 60
        force_trade = settings_manager.get("force_test_trade")

        yearly_results = []
        
        for year in range(start_year, end_year + 1):
            try:
                # Filter for the year
                year_data = df[df.index.year == year].copy()
                
                if year_data.empty:
                    logger.warning(f"⚠️ Skipping {year}: Data missing in SPY history.")
                    yearly_results.append({
                        "year": year,
                        "pnl": 0.0,
                        "trades": 0,
                        "max_drawdown": 0.0,
                        "status": "No Data"
                    })
                    continue

                # Simulation state
                daily_returns = []
                trades_count = 0
                rejection_count = 0
                debug_counter = 0
                in_position = False
                entry_price = 0
                
                # Simplified daily loop for realism
                for i in range(0, len(year_data)):
                    current_slice = year_data.iloc[max(0, i-20):i+1]
                    current_price = year_data['Close'].iloc[i]
                    current_date = year_data.index[i].strftime('%Y-%m-%d')
                    
                    if not in_position:
                        # Check for buy signal
                        score, indicators = calculate_confidence_score("SPY", current_slice, is_simulation=True)
                        if score is None or (isinstance(score, float) and np.isnan(score)): 
                            score = 0
                        
                        # DEBUG: Print the first 5 rows to see what the bot sees
                        if debug_counter < 5:
                            logger.info(f"🧐 Day {current_date}: Close=${current_price:.2f}, RSI={year_data['RSI'].iloc[i]:.2f}, Score={score}")
                            debug_counter += 1

                        # Force Trade Sanity Check
                        if force_trade and i == 0:
                            logger.warning("⚠️ FORCE TRADE EXECUTED (Sanity Check)")
                            score = 100 

                        if score >= min_threshold:
                            in_position = True
                            entry_price = current_price
                            trades_count += 1
                        else:
                            # Log first 5 rejections per year
                            if rejection_count < 5:
                                reasons = ", ".join(indicators.get('reasons', []))
                                logger.info(f"⚠️ Skipped Trade on {current_date}: Score was {score} (Threshold: {min_threshold}). Reasons: {reasons}")
                                rejection_count += 1
                    else:
                        # Check for exit (SL/TP)
                        profit_pct = (current_price - entry_price) / entry_price
                        
                        if profit_pct <= -stop_loss or profit_pct >= take_profit:
                            daily_returns.append(profit_pct)
                            in_position = False
                
                pnl = sum(daily_returns) * 100 if daily_returns else 0.0
                max_dd = year_data['Close'].pct_change().cumsum().min() * -100
                
                yearly_results.append({
                    "year": year,
                    "pnl": pnl,
                    "trades": trades_count,
                    "max_drawdown": max_dd,
                    "status": "Success"
                })

            except Exception as e:
                logger.error(f"⚠️ Error simulating {year}: {e}")
                yearly_results.append({
                    "year": year,
                    "pnl": 0.0,
                    "trades": 0,
                    "max_drawdown": 0.0,
                    "status": f"Error: {str(e)}"
                })

        return {
            "yearly": yearly_results,
            "total_return": sum(r['pnl'] for r in yearly_results),
            "settings_used": {
                "sl": stop_loss,
                "tp": take_profit,
                "threshold": min_threshold
            }
        }

    def run_historical_simulation(self):
        """Standard wrapper for UI-driven backtests (2014-2025)."""
        return self.simulate_performance(2014, 2025)

    def _generate_simulated_results(self, start_year, end_year, note):
        yearly_results = []
        for year in range(start_year, end_year + 1):
            yearly_results.append({
                "year": year,
                "pnl": 0.0,
                "trades": 0,
                "max_drawdown": 0.0,
                "status": note
            })
        return {
            "yearly": yearly_results,
            "total_return": 0.0,
            "status": "error",
            "message": note,
            "settings_used": {}
        }
