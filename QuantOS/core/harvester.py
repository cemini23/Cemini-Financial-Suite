"""
QuantOS™ v10.0.0 - BigQuery Data Harvester
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import datetime
import threading
import queue
import time
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError
from core.logger_config import get_logger

logger = get_logger("harvester")

class DataHarvester:
    """
    Cloud-native Data Harvester.
    Streams real-time market ticks directly into Google BigQuery for infinite scalability.
    """
    def __init__(self):
        # Configuration from Environment
        self.project_id = os.getenv("BQ_PROJECT_ID")
        self.dataset_id = os.getenv("BQ_DATASET_ID")
        self.table_id = os.getenv("BQ_TABLE_ID", "market_data")
        
        # Service Account Path (if set, Google Client finds it automatically from GOOGLE_APPLICATION_CREDENTIALS)
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not self.project_id or not self.dataset_id:
            logger.error("❌ BigQuery configuration missing (BQ_PROJECT_ID/BQ_DATASET_ID)!")
            self.client = None
        else:
            try:
                self.client = bigquery.Client(project=self.project_id)
                self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
                logger.info(f"🚜 HARVESTER: Connected to BigQuery -> {self.table_ref}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize BigQuery Client: {e}")
                self.client = None

        self.write_queue = queue.Queue()
        self.running = True
        self.last_tick = 0
        
        # Start background writer thread
        self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer_thread.start()
        logger.info("🚜 HARVESTER: BigQuery Streaming Thread Started.")

    def record_tick(self, symbol, price, volume):
        """Pushes tick data into the processing queue."""
        self.last_tick = time.time()
        # BigQuery expects ISO format or datetime objects for TIMESTAMP
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        row = {
            "timestamp": timestamp,
            "symbol": symbol,
            "price": float(price),
            "volume": float(volume)
        }
        self.write_queue.put(row)

    def get_status(self):
        """Returns health status."""
        if not self.client: return "MISCONFIGURED"
        if self.last_tick == 0: return "INITIALIZING"
        if time.time() - self.last_tick > 60: return "IDLE"
        return "ACTIVE"

    def _writer_loop(self):
        """Background loop to flush queue via BigQuery Streaming Inserts."""
        while self.running:
            batch = []
            while not self.write_queue.empty() and len(batch) < 500: # Batch size limit
                try:
                    batch.append(self.write_queue.get_nowait())
                except queue.Empty:
                    break
            
            if batch:
                self._flush_to_bigquery(batch)
            
            # Streaming latency: flush every 2 seconds
            time.sleep(2)

    def _flush_to_bigquery(self, rows):
        """Executes the streaming insert with error handling."""
        if not self.client:
            logger.warning(f"⚠️ HARVESTER: Client not initialized. Dropping {len(rows)} rows.")
            return

        try:
            # client.insert_rows_json(table, json_rows)
            errors = self.client.insert_rows_json(self.table_ref, rows)
            
            if errors == []:
                # logger.debug(f"✅ HARVESTER: Successfully streamed {len(rows)} rows.")
                pass
            else:
                logger.error(f"❌ HARVESTER: BigQuery Insert Errors: {errors}")
        except GoogleAPICallError as e:
            logger.error(f"❌ HARVESTER: BigQuery API Error: {e}")
        except Exception as e:
            logger.error(f"❌ HARVESTER: Unexpected flush error: {e}")

    def stop(self):
        """Graceful shutdown."""
        self.running = False
        self.writer_thread.join(timeout=5)
        logger.info("🚜 HARVESTER: Stopped.")

# Singleton instance
harvester = DataHarvester()
