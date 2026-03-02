---
name: async-python-patterns
version: 1.2.0
description: Best practices for async Python with asyncio — structured concurrency, timeouts, and task management.
tags: [python, async, asyncio, performance, concurrency]
author: wshobson
---

# Async Python Patterns

This skill teaches production-grade asyncio patterns for Python 3.10+.

## Core Concepts

### Gathering concurrent tasks

Use `asyncio.gather()` to run multiple coroutines concurrently and collect results:

```python
import asyncio

async def fetch_price(symbol: str) -> float:
    await asyncio.sleep(0.1)   # simulate I/O
    return 42.0

async def main():
    prices = await asyncio.gather(
        fetch_price("AAPL"),
        fetch_price("MSFT"),
        fetch_price("TSLA"),
    )
    print(prices)
```

### Timeouts

Always bound async operations with timeouts to prevent hangs:

```python
async with asyncio.timeout(30):
    result = await slow_operation()
```

For Python < 3.11 use `asyncio.wait_for`:

```python
result = await asyncio.wait_for(slow_operation(), timeout=30)
```

### Structured concurrency with TaskGroup

`asyncio.TaskGroup` (Python 3.11+) propagates errors correctly:

```python
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(worker_a())
    t2 = tg.create_task(worker_b())
# Both tasks complete (or both are cancelled on error) before continuing
```

### Avoiding common mistakes

- Do not mix `asyncio.run()` and `loop.run_until_complete()` — pick one.
- Never `await` inside a list comprehension without wrapping in `asyncio.gather`.
- Use `asyncio.Lock` for shared mutable state, not threading primitives.
- Prefer `async for` over buffering entire async iterators into memory.

## Error Handling

```python
async def safe_fetch(symbol: str):
    try:
        return await fetch_price(symbol)
    except asyncio.TimeoutError:
        return None
    except Exception as exc:
        logger.error("fetch failed for %s: %s", symbol, exc)
        return None
```

## Testing Async Code

Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pyproject.toml`.

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_price():
    price = await fetch_price("AAPL")
    assert price > 0
```
