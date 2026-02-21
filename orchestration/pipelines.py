import dagster as dg
import polars as pl
from core.storage.arctic_manager import historical_storage
import os

@dg.asset(group_name="maintenance", compute_kind="Polars")
def cold_storage_sync():
    """
    Moves data from QuestDB (Hot) to ArcticDB (Cold).
    Runs nightly to keep the real-time database lean.
    """
    # 1. Connect to QuestDB
    quest_host = os.getenv("QUESTDB_HOST", "questdb")
    conn = f"postgresql://admin:quest@{quest_host}:8812/qdb"
    
    # 2. Extract yesterday's data
    query = "SELECT * FROM raw_market_ticks WHERE timestamp < now() - 1d"
    
    try:
        df_to_move = pl.read_database(query=query, connection=conn)
        
        if not df_to_move.is_empty():
            print(f"📦 Dagster: Moving {len(df_to_move)} rows to cold storage...")
            # 3. Append to ArcticDB
            historical_storage.write_df("tick_history_master", df_to_move)
            
            # 4. Return success metadata for Dagster UI
            return dg.AssetCheckResult(passed=True, metadata={"rows_synced": len(df_to_move)})
        
        return dg.AssetCheckResult(passed=True, metadata={"status": "No data to sync"})
        
    except Exception as e:
        print(f"❌ Dagster Sync Failed: {e}")
        raise e

# Schedule to run at midnight
sync_schedule = dg.ScheduleDefinition(
    name="nightly_cold_sync",
    target=dg.AssetSelection.assets(cold_storage_sync), 
    cron_schedule="0 0 * * *"
)

# Combined Definitions
defs = dg.Definitions(
    assets=[cold_storage_sync],
    schedules=[sync_schedule],
)
