import polars as pl
import os

def get_market_context(symbol: str, timeframe_minutes: int = 15):
    """
    Queries QuestDB, aggregates ticks into OHLCV via Polars,
    and returns a string context for the LLM.
    """
    db_host = os.getenv("QUESTDB_HOST", "questdb")
    db_user = os.getenv("QUESTDB_USER", "admin")
    db_pass = os.getenv("QUESTDB_PASSWORD", "quest")
    conn = f"postgresql://{db_user}:{db_pass}@{db_host}:8812/qdb"

    # Query raw ticks for the specific symbol
    query = f"""
    SELECT timestamp, price, volume
    FROM raw_market_ticks
    WHERE symbol = '{symbol}'
    AND timestamp > now() - {timeframe_minutes}m;
    """

    try:
        # Load into Polars DataFrame
        lf = pl.read_database(query=query, connection=conn).lazy()

        # Aggregate ticks into 1-minute OHLCV bars
        ohlcv = (
            lf.with_columns(pl.col("timestamp").dt.truncate("1m"))
            .group_by("timestamp")
            .agg([
                pl.col("price").first().alias("open"),
                pl.col("price").max().alias("high"),
                pl.col("price").min().alias("low"),
                pl.col("price").last().alias("close"),
                pl.col("volume").sum().alias("volume"),
            ])
            .sort("timestamp")
            .collect()
        )

        if ohlcv.is_empty():
            return "No recent market data found for this symbol."

        # Convert to a compact string for the LLM context (token efficient)
        return ohlcv.to_pandas().to_string(index=False)
    except Exception as e:
        return f"Error retrieving market context: {e}"

# This output is then injected into the LangGraph state:
# state['raw_market_data'] = get_market_context("BTC-USD")
