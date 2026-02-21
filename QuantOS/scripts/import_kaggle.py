import pandas as pd
import glob
import os
import ta
from datetime import datetime
from core.logger_config import get_logger

logger = get_logger("kaggle_importer")

IMPORT_DIR = 'data/kaggle_import'
OUTPUT_FILE = 'data/ml_training_data.csv'

# Only process these tickers (standard watchlist)
TARGET_TICKERS = ['SPY', 'QQQ', 'NVDA', 'AMD', 'MSFT', 'AMZN', 'AFRM', 'UPST', 'HIMS', 'LYFT', 'DASH', 'NFLX', 'ACAD']

def process_kaggle_data():
    # Recursive scan for both .csv and .txt files
    files = []
    for root, dirs, filenames in os.walk(IMPORT_DIR):
        for filename in filenames:
            if filename.endswith(('.csv', '.txt')):
                files.append(os.path.join(root, filename))
    
    if not files:
        logger.info(f"No CSV or TXT files found in {IMPORT_DIR}")
        return

    all_processed_data = []

    for file_path in files:
        logger.info(f"Checking {file_path}...")
        try:
            # All files appear to be CSV-formatted with headers
            df = pd.read_csv(file_path)
            
            # Map columns for CSVs with headers
            col_map = {}
            for col in df.columns:
                lower_col = str(col).lower()
                if 'date' in lower_col or 'time' in lower_col: col_map[col] = 'Timestamp'
                if 'open' in lower_col: col_map[col] = 'Open'
                if 'high' in lower_col: col_map[col] = 'High'
                if 'low' in lower_col: col_map[col] = 'Low'
                if 'close' in lower_col: col_map[col] = 'Close'
                if 'vol' in lower_col: col_map[col] = 'Volume'
                if 'ticker' in lower_col or 'symbol' in lower_col: col_map[col] = 'Ticker'

            df = df.rename(columns=col_map)
            
            # Handle multi-ticker files vs single-ticker files
            if 'Ticker' in df.columns:
                # Filter for target tickers first to save processing time
                df['Ticker'] = df['Ticker'].astype(str).str.upper()
                df = df[df['Ticker'].isin(TARGET_TICKERS)]
                if df.empty:
                    continue
                
                # Group by ticker to calculate indicators correctly for each
                tickers_in_file = df['Ticker'].unique()
                for t in tickers_in_file:
                    ticker_df = df[df['Ticker'] == t].copy()
                    process_single_dataframe(ticker_df, t, all_processed_data)
            else:
                # Single ticker file - extract from filename
                # Handles "AAPL.csv", "aapl.us.txt", "AAPL_data.csv", etc.
                raw_name = os.path.basename(file_path).upper()
                # Remove common suffixes and extensions
                ticker = raw_name.replace('_DATA', '').replace('.US', '').split('.')[0]
                
                if ticker in TARGET_TICKERS:
                    process_single_dataframe(df, ticker, all_processed_data)

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

def process_single_dataframe(df, ticker, all_processed_data):
    try:
        # Required columns check
        required = ['Timestamp', 'Close']
        if not all(col in df.columns for col in required):
            logger.warning(f"Skipping {ticker}: Missing required columns")
            return

        # Sort by date for indicator calculation
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
        df = df.sort_values('Timestamp')

        # Calculate Indicators
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        macd_obj = ta.trend.MACD(df['Close'])
        df['MACD'] = macd_obj.macd()
        
        # Fill NaNs
        df = df.fillna(0)

        # Prepare for ML Training Data format
        processed = pd.DataFrame()
        processed['Timestamp'] = df['Timestamp'] # Keep as datetime object
        processed['Ticker'] = ticker
        processed['Price'] = df['Close']
        processed['RSI'] = df['RSI']
        processed['MACD'] = df['MACD']
        processed['Volume'] = df['Volume'] if 'Volume' in df.columns else 0
        processed['Action'] = "HISTORICAL"
        processed['Confidence_Score'] = 0

        all_processed_data.append(processed)
        logger.info(f"Successfully processed {len(processed)} rows for {ticker}")
    except Exception as e:
        logger.error(f"Error processing dataframe for {ticker}: {e}")

    if all_processed_data:
        new_data_df = pd.concat(all_processed_data)
        
        # Load existing data if it exists
        if os.path.exists(OUTPUT_FILE):
            existing_df = pd.read_csv(OUTPUT_FILE)
            existing_df['Timestamp'] = pd.to_datetime(existing_df['Timestamp'], format='mixed')
            combined_df = pd.concat([existing_df, new_data_df])
        else:
            combined_df = new_data_df
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        # Sort by Timestamp to ensure a clean timeline
        combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'], format='mixed')
        combined_df = combined_df.sort_values('Timestamp')

        # Deduplicate
        original_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['Timestamp', 'Ticker'], keep='first')
        removed_count = original_count - len(combined_df)

        # Format output for consistency
        combined_df['Timestamp'] = combined_df['Timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Save back to CSV
        combined_df.to_csv(OUTPUT_FILE, index=False)
        
        logger.info(f"Process complete.")
        logger.info(f"✅ Removed {removed_count} duplicate rows.")
        logger.info(f"✅ Final dataset contains {len(combined_df)} total rows in {OUTPUT_FILE}")
    else:
        logger.info("No data was processed.")

if __name__ == "__main__":
    process_kaggle_data()
