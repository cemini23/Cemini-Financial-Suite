import os
from google.cloud import bigquery

def setup_bigquery_environment():
    # 1. Verify Authentication
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("⚠️ ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable is missing.")
        print("Please point it to your downloaded Google Cloud JSON key.")
        return

    # Initialize the client (it automatically picks up the credentials and project ID)
    client = bigquery.Client()
    project_id = client.project
    
    # 2. Define Names
    dataset_name = "quantos_live"
    table_name = "market_ticks"
    
    dataset_id = f"{project_id}.{dataset_name}"
    table_id = f"{dataset_id}.{table_name}"

    # 3. Provision the Dataset
    print(f"📦 Provisioning Dataset: {dataset_id}...")
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US" # You can change this to your preferred Google Cloud region
    
    try:
        # exists_ok=True prevents the script from crashing if you run it twice
        dataset = client.create_dataset(dataset, exists_ok=True)
        print("✅ Dataset is online.")
    except Exception as e:
        print(f"❌ Failed to create dataset: {e}")
        return

    # 4. Provision the Table with Schema
    print(f"📊 Building Table Schema: {table_id}...")
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", description="Time of the tick"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED", description="Ticker symbol"),
        bigquery.SchemaField("price", "FLOAT", mode="REQUIRED", description="Execution price"),
        bigquery.SchemaField("volume", "FLOAT", mode="REQUIRED", description="Number of shares/contracts")
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    
    # Optimize costs by partitioning the data by day
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="timestamp"
    )

    try:
        table = client.create_table(table, exists_ok=True)
        print("✅ Table architecture is locked in.")
        
        print("\n🚀 SUCCESS! Add these lines to your .env file:")
        print("--------------------------------------------------")
        print(f"BQ_PROJECT_ID={project_id}")
        print(f"BQ_DATASET_ID={dataset_name}")
        print(f"BQ_TABLE_ID={table_name}")
        print("--------------------------------------------------")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")

if __name__ == "__main__":
    setup_bigquery_environment()
