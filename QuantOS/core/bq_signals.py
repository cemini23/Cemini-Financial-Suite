"""
QuantOS™ v12.1.0 - BigQuery Signal Engine (Refined)
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import time
import threading
from google.cloud import bigquery
from core.logger_config import get_logger

logger = get_logger("bq_signals")

class CloudSignalEngine:
    """
    Cloud-native Momentum & Volatility Ranker.
    Polls Google BigQuery every 60 seconds for top market movers and volume spikes.
    """
    def __init__(self):
        # Authenticates automatically using GOOGLE_APPLICATION_CREDENTIALS in .env
        self.project_id = os.getenv("BQ_PROJECT_ID")
        self.dataset = os.getenv("BQ_DATASET_ID")
        self.table = os.getenv("BQ_TABLE_ID", "market_ticks")
        
        if not self.project_id or not self.dataset:
            logger.error("❌ BigQuery configuration missing for CloudSignalEngine!")
            self.client = None
        else:
            try:
                self.client = bigquery.Client(project=self.project_id)
                self.full_table_path = f"{self.project_id}.{self.dataset}.{self.table}"
                logger.info(f"☁️  CLOUD ENGINE: Connected to BigQuery -> {self.full_table_path}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize BigQuery Client: {e}")
                self.client = None

        self.latest_signals = {"top_movers": [], "volume_spikes": []}
        self.running = True
        
        if self.client:
            # Start background polling thread
            self.poller_thread = threading.Thread(target=self._poll_cloud_data, daemon=True)
            self.poller_thread.start()
            logger.info("📡 SIGNAL UPDATE: Cloud Polling Thread Started (60s Intervals).")

    def _poll_cloud_data(self):
        """Runs the SQL queries every 60 seconds without blocking the main bot."""
        while self.running:
            try:
                self._update_top_movers()
                self._update_volume_spikes()
            except Exception as e:
                logger.error(f"⚠️  BigQuery Polling Error: {e}")
            
            time.sleep(60) 

    def _update_volume_spikes(self):
        """Detects 300%+ volume spikes and calculates the 5-minute price change."""
        if not self.client:
            return

        query = f"""
        WITH RecentData AS (
          SELECT 
            symbol,
            -- Get the first and last price of the last 5 minutes
            ARRAY_AGG(price ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] AS open_5m,
            ARRAY_AGG(price ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] AS close_5m,
            SUM(volume) AS vol_5m 
          FROM `{self.full_table_path}`
          WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
          GROUP BY symbol
        ),
        AverageVolume AS (
          SELECT 
            symbol, 
            SUM(volume) / 12 AS avg_vol_5m -- 1 hour avg divided into 5-min chunks
          FROM `{self.full_table_path}`
          WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
          GROUP BY symbol
        )
        SELECT 
          r.symbol, 
          ROUND((r.vol_5m / NULLIF(a.avg_vol_5m, 0)), 2) AS volume_multiplier,
          ROUND(((r.close_5m - r.open_5m) / NULLIF(r.open_5m, 0)) * 100, 2) AS price_change_5m
        FROM 
          RecentData r
        JOIN 
          AverageVolume a ON r.symbol = a.symbol
        WHERE 
          r.vol_5m > (a.avg_vol_5m * 3) -- Only return if volume is 3x normal
        ORDER BY 
          volume_multiplier DESC;
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            # Store the spikes in memory for the main engine to read
            self.latest_signals['volume_spikes'] = [
                {
                    "symbol": row.symbol, 
                    "multiplier": row.volume_multiplier,
                    "price_change_5m": row.price_change_5m
                } 
                for row in results
            ]
            if self.latest_signals['volume_spikes']:
                logger.info(f"🚨 SPIKE ALERT: {self.latest_signals['volume_spikes']}")
        except Exception as e:
            logger.error(f"❌ BigQuery Spike Update Error: {e}")

    def _update_top_movers(self):
        """Executes the daily volatility ranker on BigQuery."""
        if not self.client:
            return

        query = f"""
        WITH daily_stats AS (
          SELECT
            symbol,
            ARRAY_AGG(price ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] AS open_price,
            ARRAY_AGG(price ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] AS close_price,
            SUM(volume) AS total_volume
          FROM `{self.full_table_path}`
          WHERE DATE(timestamp, 'America/New_York') = CURRENT_DATE('America/New_York')
          GROUP BY symbol
        )
        SELECT
          symbol,
          ROUND(((close_price - open_price) / NULLIF(open_price, 0)) * 100, 2) AS percent_change
        FROM daily_stats
        ORDER BY ABS(percent_change) DESC
        LIMIT 5;
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            self.latest_signals['top_movers'] = [
                {"symbol": row.symbol, "change": row.percent_change} for row in results
            ]
            
            if self.latest_signals['top_movers']:
                logger.info(f"📡 SIGNAL REFRESH: {self.latest_signals['top_movers']}")
        except Exception as e:
            logger.error(f"❌ BigQuery Mover Update Error: {e}")

    def get_current_signals(self):
        """Thread-safe access to the latest signals for the main TradingEngine."""
        return self.latest_signals

    def stop(self):
        """Gracefully stop polling."""
        self.running = False
        logger.info("☁️  CLOUD ENGINE: Polling stopped.")

# Instance for engine-wide access
cloud_signals = CloudSignalEngine()
