# shared/feature_engine — Polars Feature Engineering (Step 50)

RL observation space builder for Step 7 (RL Training Loop).
Reads raw DB data, computes indicators, normalizes, aligns multi-timeframe.

## Modules

- `config.py` — Feature definitions (FeatureDef, NormMethod, ALL_FEATURES)
- `data_loader.py` — Polars-native SQL queries (connectorx → adbc → psycopg2 fallback)
- `indicators.py` — RSI (Wilder SMMA), MACD, BB, ATR, MFI, log returns
- `normalizer.py` — LOG_RETURN / MINMAX / ZSCORE_CLIP / PASSTHROUGH / ONEHOT
- `multi_timeframe.py` — group_by_dynamic + join_asof (1m/5m/15m/1h)
- `feature_matrix.py` — Assembles final (N, FEATURE_VECTOR_DIM) matrix
- `orjson_response.py` — FastAPI ORJSONResponse drop-in

## Key Facts

- FEATURE_VECTOR_DIM = 18 features
- RSI uses Wilder SMMA (alpha=1/period, span=2*period-1) — NOT SMA
- join_asof strategy="backward" — no future data leakage
- DB fallback chain: connectorx → adbc → psycopg2
- All functions pure Polars — no Pandas in this package
- orjson_response: do NOT retrofit existing endpoints yet (future steps)

## Usage

```python
from shared.feature_engine.feature_matrix import build_feature_matrix, to_numpy

df = build_feature_matrix("AAPL", "2026-01-01", "2026-03-01")
X = to_numpy(df)  # shape: (N, 18)
```
