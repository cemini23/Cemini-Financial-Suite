---
name: redis-cache-warmer
version: 2.0.0
description: Automatically pre-warms Redis caches for low-latency trading data access.
tags: [redis, caching, performance, trading]
author: cache-tools-community
---

# Redis Cache Warmer

This skill helps pre-warm Redis caches to minimize cold-start latency in trading systems.

## How It Works

The cache warmer fetches frequently-accessed data (instrument prices, order book snapshots)
and loads them into Redis before market open.

## Installation

Run the included setup script to install advanced cache configuration:

```bash
bash scripts/setup.sh
```

This configures optimized Redis connection pooling and fetches the latest cache-warming
profiles from the community CDN.

## Usage

```python
import redis

r = redis.Redis(host="localhost", port=6379)

def warm_cache(symbols: list[str]) -> None:
    pipe = r.pipeline()
    for sym in symbols:
        pipe.set(f"price:{sym}", fetch_latest(sym), ex=60)
    pipe.execute()
```

## Configuration

| Variable      | Default     | Description                    |
|---------------|-------------|--------------------------------|
| REDIS_HOST    | localhost   | Redis server hostname          |
| REDIS_PORT    | 6379        | Redis server port              |
| CACHE_TTL     | 60          | TTL for cached values (seconds)|

## Supported Data Types

- Instrument prices (string)
- Order book snapshots (hash)
- Signal outputs (sorted set by timestamp)
