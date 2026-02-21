
import pytest
import numpy as np
from core.brain import QuantBrain

def test_rsi_calculation():
    # TEST: Does the RSI math handle a vertical move correctly?
    brain = QuantBrain()
    # Feed it 14 days of constant growth
    for i in range(20):
        brain.update_price("SPY", 100 + i)
    
    rsi = brain.calculate_rsi("SPY")
    assert rsi > 70  # Should be Overbought
    print(f"\n✅ RSI Math Check: {rsi}")

def test_empty_data_handling():
    # TEST: Does the bot crash if there is no data?
    brain = QuantBrain()
    rsi = brain.calculate_rsi("NON_EXISTENT")
    assert rsi == 50.0  # Should return neutral default
    print("✅ Empty Data Handling: Safe")

def test_numpy_integration():
    # TEST: Is the data actually being stored as high-speed numpy arrays?
    brain = QuantBrain()
    brain.update_price("QQQ", 380.0)
    assert isinstance(brain.price_history["QQQ"], np.ndarray)
    print("✅ Numpy Integration Check: Verified")
