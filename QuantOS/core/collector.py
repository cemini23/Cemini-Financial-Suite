import csv
import os
from datetime import datetime
from core.logger_config import get_logger

logger = get_logger("collector")

class DataCollector:
    def __init__(self, file_path='data/ml_training_data.csv'):
        self.file_path = file_path
        self.headers = ['Timestamp', 'Ticker', 'Price', 'RSI', 'MACD', 'Volume', 'Action', 'Confidence_Score']
        self._init_file()

    def _init_file(self):
        if not os.path.exists(self.file_path):
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, mode='w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.headers)
                logger.info(f"Initialized ML data file: {self.file_path}")
            except Exception as e:
                logger.error(f"Failed to initialize ML data file: {e}")

    def log_state(self, ticker, current_price, indicators_dict, action_taken):
        """
        Appends a row of trading data to the ML training CSV.
        indicators_dict: {'rsi': val, 'macd': val, 'volume': val, 'score': val}
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [
            timestamp,
            ticker,
            current_price,
            indicators_dict.get('rsi', 0),
            indicators_dict.get('macd', 0),
            indicators_dict.get('volume', 0),
            action_taken,
            indicators_dict.get('score', 0)
        ]

        with open(self.file_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
