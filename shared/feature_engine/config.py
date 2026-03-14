"""
Feature space definition for Step 7 RL Training Loop.
Each agent's observation vector is constructed from these features.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NormMethod(Enum):
    LOG_RETURN = "log_return"
    MINMAX = "minmax"
    ZSCORE_CLIP = "zscore_clip"
    ONEHOT = "onehot"
    PASSTHROUGH = "passthrough"


@dataclass
class FeatureDef:
    name: str
    source_table: str
    source_column: str
    norm_method: NormMethod
    lookback_window: int = 0
    description: str = ""


MOMENTUM_FEATURES: list[FeatureDef] = [
    FeatureDef("rsi_14", "raw_market_ticks", "close", NormMethod.MINMAX, 14, "RSI(14) Wilder SMMA"),
    FeatureDef("macd_signal", "raw_market_ticks", "close", NormMethod.ZSCORE_CLIP, 0, "MACD signal line"),
    FeatureDef("macd_histogram", "raw_market_ticks", "close", NormMethod.ZSCORE_CLIP, 0, "MACD histogram"),
]

VOLATILITY_FEATURES: list[FeatureDef] = [
    FeatureDef("bb_width", "raw_market_ticks", "close", NormMethod.ZSCORE_CLIP, 20, "Bollinger Band width"),
    FeatureDef("atr_14", "raw_market_ticks", "close", NormMethod.ZSCORE_CLIP, 14, "ATR(14)"),
]

PARTICIPATION_FEATURES: list[FeatureDef] = [
    FeatureDef("volume_zscore", "raw_market_ticks", "volume", NormMethod.ZSCORE_CLIP, 20, "Volume Z-score"),
    FeatureDef("mfi_14", "raw_market_ticks", "close", NormMethod.MINMAX, 14, "MFI(14)"),
]

SENTIMENT_FEATURES: list[FeatureDef] = [
    FeatureDef("fgi_normalized", "macro_logs", "fear_greed_index", NormMethod.MINMAX, 0, "Fear & Greed Index"),
    FeatureDef("finbert_sentiment", "sentiment_logs", "sentiment_score", NormMethod.PASSTHROUGH, 0, "FinBERT sentiment"),
]

MACRO_FEATURES: list[FeatureDef] = [
    FeatureDef("treasury_10y", "macro_logs", "treasury_yield", NormMethod.ZSCORE_CLIP, 0, "10Y Treasury yield"),
    FeatureDef("yield_curve_spread", "fred_data", "T10Y2Y", NormMethod.ZSCORE_CLIP, 0, "10Y-2Y spread"),
    FeatureDef("credit_spread", "fred_data", "BAMLH0A0HYM2", NormMethod.ZSCORE_CLIP, 0, "HY OAS spread"),
]

REGIME_FEATURES: list[FeatureDef] = [
    FeatureDef("regime_green", "playbook_logs", "regime", NormMethod.ONEHOT, 0, "Regime=GREEN"),
    FeatureDef("regime_yellow", "playbook_logs", "regime", NormMethod.ONEHOT, 0, "Regime=YELLOW"),
    FeatureDef("regime_red", "playbook_logs", "regime", NormMethod.ONEHOT, 0, "Regime=RED"),
]

PRICE_FEATURES: list[FeatureDef] = [
    FeatureDef("log_return_1m", "raw_market_ticks", "close", NormMethod.LOG_RETURN, 1, "1-min log return"),
    FeatureDef("log_return_5m", "raw_market_ticks", "close", NormMethod.LOG_RETURN, 5, "5-min log return"),
    FeatureDef("log_return_1h", "raw_market_ticks", "close", NormMethod.LOG_RETURN, 60, "1-hour log return"),
]

ALL_FEATURES: list[FeatureDef] = (
    MOMENTUM_FEATURES
    + VOLATILITY_FEATURES
    + PARTICIPATION_FEATURES
    + SENTIMENT_FEATURES
    + MACRO_FEATURES
    + REGIME_FEATURES
    + PRICE_FEATURES
)

FEATURE_VECTOR_DIM: int = len(ALL_FEATURES)

TIMEFRAMES: dict[str, int] = {
    "1h": 60,
    "15m": 15,
    "5m": 5,
    "1m": 1,
}
