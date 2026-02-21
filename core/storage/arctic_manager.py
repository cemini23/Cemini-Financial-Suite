import polars as pl
import numpy as np
from arcticdb import Arctic
import os

class ArcticDBManager:
    """
    Manages the bitemporal historical storage using ArcticDB.
    Bridges Polars ingestion with versioned DataFrame storage.
    """
    def __init__(self, uri: str = "lmdb:///data/arcticdb"):
        self.ac = Arctic(uri)
        self.library_name = 'quantos_historical'
        
        # Ensure library exists
        if self.library_name not in self.ac.list_libraries():
            self.ac.create_library(self.library_name)
        
        self.library = self.ac[self.library_name]

    def write_df(self, symbol: str, df: pl.DataFrame):
        """
        Commits a Polars DataFrame to ArcticDB.
        Handles conversion to Pandas (ArcticDB requirement) internally.
        """
        # ArcticDB requires a datetime index for time-series optimizations
        pandas_df = df.to_pandas()
        if 'timestamp' in pandas_df.columns:
            pandas_df.set_index('timestamp', inplace=True)
        
        self.library.write(symbol, pandas_df)
        print(f"✅ ArcticDB: [{symbol}] versioned and committed.")

    def read_to_numpy(self, symbol: str, columns: list = ['close']) -> np.ndarray:
        """
        Reads specific columns directly from storage into NumPy for VectorBT.
        Extremely memory efficient as it avoids loading the full DataFrame.
        """
        try:
            item = self.library.read(symbol, columns=columns)
            return item.data[columns[0]].to_numpy()
        except Exception as e:
            print(f"❌ ArcticDB Read Error for {symbol}: {e}")
            return np.array([])

    def get_versions(self, symbol: str):
        """Returns all historical versions of the dataset for time-travel."""
        return self.library.list_versions(symbol)

# Global Instance
historical_storage = ArcticDBManager()
