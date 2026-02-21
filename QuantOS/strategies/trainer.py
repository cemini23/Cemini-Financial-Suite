import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
from core.logger_config import get_logger

logger = get_logger("trainer")

def train_model():
    file_path = 'data/ml_training_data.csv'
    model_path = 'model_v1.pkl'

    # 1. LOAD DATA
    if not os.path.exists(file_path):
        logger.error(f"{file_path} not found.")
        return

    df = pd.read_csv(file_path)

    # 2. CHECK DATA SIZE
    if len(df) < 100:
        logger.warning(f"Not enough data to train yet (Current: {len(df)} rows, Need 100+)")
        return

    logger.info(f"Training model on {len(df)} rows...")

    # 3. LABELING (Target: Price up > 1% in the near future)
    # We use shift(-5) to look 5 records ahead for the same ticker
    df['Future_Price'] = df.groupby('Ticker')['Price'].shift(-5)
    df['Target'] = ((df['Future_Price'] - df['Price']) / df['Price'] > 0.01).astype(int)

    # Drop rows where we don't have future data (the last 5 rows per ticker)
    df = df.dropna(subset=['Future_Price'])

    # 4. FEATURES
    features = ['RSI', 'MACD', 'Volume']
    X = df[features]
    y = df['Target']

    # 5. TRAIN
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Use RandomForest (more portable than XGBoost without brew/libomp)
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # 6. SAVE & REPORT
    joblib.dump(model, model_path)
    
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    logger.info(f"Training Complete! Accuracy: {accuracy * 100:.2f}%")
    logger.info(f"Model saved to: {model_path}")

if __name__ == "__main__":
    train_model()
