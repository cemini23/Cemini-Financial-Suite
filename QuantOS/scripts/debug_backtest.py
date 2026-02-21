"""
QuantOS™ v6.0 - Backtest Debugger
Runs the simulation for problematic years and prints tracebacks.
"""
import sys
import os
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.backtester import BacktestEngine

def run_debug():
    print("🔬 Starting Debug Backtest for 2014-2015...")
    try:
        engine = BacktestEngine()
        results = engine.simulate_performance(2014, 2015)
        
        print("\n✅ Simulation Completed.")
        if "total_return" in results:
            print(f"Total Return: {results.get('total_return'):.2f}%")
        if "yearly" in results:
            for res in results.get('yearly', []):
                print(f"Year {res['year']}: PnL {res['pnl']:.2f}%, Status: {res.get('status', 'N/A')}")
        if "note" in results:
            print(f"Note: {results['note']}")
            
    except Exception:
        print("\n❌ CRITICAL CRASH DETECTED:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_debug()
