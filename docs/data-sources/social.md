# Social & Sentiment Data

The social sentiment pipeline harvests Twitter/X posts and applies FinBERT NLP scoring to generate market sentiment signals. It is gated behind the `SOCIAL_ALPHA_LIVE` safety guard (C5).

---

## Role

- Continuous harvesting of financial Twitter/X content
- FinBERT sentiment scoring (positive/negative/neutral per post)
- Aggregate sentiment score published to Intel Bus
- Elon Musk tweet velocity model (MuskPredictor in Kalshi engine)

---

## social_scraper Service

The `social_scraper` service monitors approximately 62 tracked X accounts (configured in `scrapers/x_harvester.py`). It uses the Twitter/X API with rate limit awareness.

**FinBERT model:** Financial domain fine-tuned BERT, hosted via Hugging Face `transformers` library. Model is lazy-loaded and cached as a singleton to avoid repeated initialization overhead.

---

## Safety Guard C5

```bash
# Required to enable live social signals:
SOCIAL_ALPHA_LIVE=true
```

When `SOCIAL_ALPHA_LIVE` is not `true`, the social analyzer returns a neutral signal (0.5 sentiment) regardless of actual tweet content. This prevents unvalidated social signals from influencing live trading.

**Rationale:** Social signals have the lowest source weight (0.40) in the conviction scorer but the highest noise-to-signal ratio. The guard ensures they only contribute when explicitly enabled by the operator.

---

## FinBERT Integration

```python
# From QuantOS/brain/quant_brain.py (simplified)
from transformers import pipeline

_sentiment_pipeline = None

def get_sentiment_score(text: str) -> float:
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline("text-classification",
                                       model="ProsusAI/finbert")
    result = _sentiment_pipeline(text[:512])[0]
    # Map: positive→1.0, neutral→0.5, negative→0.0
    mapping = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
    return mapping[result["label"].lower()]
```

---

## Intel Bus Output

```
intel:sentiment_score → float (0.0 – 1.0)
TTL: 600s
Refresh: ~10 min (or on significant new post)
```

Values above 0.65 are considered bullish; below 0.35 are bearish.
