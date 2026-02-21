import unittest
import numpy as np
from core.brain import QuantBrain

class TestQuantOS(unittest.TestCase):
    def test_rsi_calculation(self):
        # TEST: Does the RSI math handle a vertical move correctly?
        brain = QuantBrain()
        # Feed it 20 days of constant growth
        for i in range(20):
            brain.update_price("SPY", 100 + i)
        
        rsi = brain.calculate_rsi("SPY")
        print(f"\n[DEBUG] RSI calculated: {rsi:.2f}")
        self.assertGreater(rsi, 70, "RSI should be overbought (> 70) for constant growth")

    def test_empty_data_handling(self):
        # TEST: Does the bot crash if there is no data?
        brain = QuantBrain()
        rsi = brain.calculate_rsi("NON_EXISTENT")
        self.assertEqual(rsi, 50.0, "Should return neutral default (50.0) for missing data")

    def test_numpy_integration(self):
        # TEST: Is the data actually being stored as high-speed numpy arrays?
        brain = QuantBrain()
        brain.update_price("QQQ", 380.0)
        self.assertIsInstance(brain.price_history["QQQ"], np.ndarray, "History should be a numpy array")

if __name__ == '__main__':
    unittest.main()
