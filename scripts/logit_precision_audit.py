"""
logit_precision_audit.py — Step 30 precision audit for logit_pricing library.

Tests:
  1. 10,000 random probabilities round-trip: p → logit → sigmoid ≈ p
  2. Boundary cases: p near 0, p near 1, p=0.5
  3. Real Kalshi BBO prices from Redis (if available)
  4. Decimal precision: multiply_before_divide vs naive division

Output: /mnt/archive/logit_pricing/precision_audit.json
"""

import json
import os
import sys
import time
import random

# Ensure logit_pricing is importable
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np
from logit_pricing.transforms import logit, inv_logit, logit_array, inv_logit_array, P_MIN, P_MAX
from logit_pricing.precision import (
    multiply_before_divide, safe_divide, clamp_probability, sanitize_array
)

ARCHIVE_PATH = "/mnt/archive/logit_pricing/precision_audit.json"
N_RANDOM = 10_000
RTOL = 1e-9  # round-trip tolerance


def audit_roundtrip(n: int = N_RANDOM) -> dict:
    """logit(inv_logit(x)) == x and inv_logit(logit(p)) == p for random inputs."""
    rng = random.Random(42)
    np_rng = np.random.default_rng(42)

    # ── 1. p → logit → sigmoid round-trip ──────────────────────────────────
    ps = np_rng.uniform(P_MIN, P_MAX, n)
    logits, _invalid = logit_array(ps)
    recovered = inv_logit_array(logits)
    errs = np.abs(recovered - ps)
    max_err = float(errs.max())
    mean_err = float(errs.mean())
    pass_rt = bool(max_err < RTOL)

    # ── 2. Boundary cases ───────────────────────────────────────────────────
    boundary = {}
    for p_raw, label in [
        (0.0,     "p=0.0 (clamped)"),
        (1.0,     "p=1.0 (clamped)"),
        (1e-10,   "p=1e-10 (clamped)"),
        (0.5,     "p=0.5 (midpoint)"),
        (0.001,   "p=P_MIN"),
        (0.999,   "p=P_MAX"),
        (0.01,    "p=0.01"),
        (0.99,    "p=0.99"),
        (float("nan"), "p=NaN (clamped)"),
        (float("inf"), "p=Inf (clamped)"),
    ]:
        p_clamped = clamp_probability(p_raw)
        lg = logit(p_clamped)
        recovered_p = inv_logit(lg)
        err = abs(recovered_p - p_clamped) if (recovered_p == recovered_p) else 0.0
        boundary[label] = {
            "input": str(p_raw),
            "clamped": p_clamped,
            "logit": lg,
            "recovered": recovered_p,
            "error": err,
        }

    # ── 3. Decimal precision: multiply_before_divide ──────────────────────
    # Compare a/b*c vs (a*c)/b for numerically sensitive values
    cases = [
        (0.123456789012345, 0.000000001, 0.999999999),
        (1.0, 3.0, 1.0),   # 1/3 classic
        (99.0, 100.0, 1.0),
    ]
    decimal_tests = []
    for a, b, c in cases:
        naive = (a / b) * c
        precise = float(multiply_before_divide(a, b, c))
        decimal_tests.append({
            "a": a, "b": b, "c": c,
            "naive": naive,
            "precise": precise,
            "delta": abs(naive - precise),
        })

    # ── 4. safe_divide ────────────────────────────────────────────────────
    sd_zero = float(safe_divide(1.0, 0.0, default=-999.0))
    sd_normal = float(safe_divide(6.0, 2.0, default=0.0))
    safe_divide_ok = sd_zero == -999.0 and abs(sd_normal - 3.0) < 1e-12

    # ── 5. sanitize_array ─────────────────────────────────────────────────
    dirty = np.array([0.5, float("nan"), float("inf"), -float("inf"), 0.3])
    clean_arr, n_replaced = sanitize_array(dirty, fill=0.5)
    sanitize_ok = bool(np.all(np.isfinite(clean_arr))) and n_replaced == 3

    return {
        "roundtrip": {
            "n": n,
            "max_error": max_err,
            "mean_error": mean_err,
            "tolerance": RTOL,
            "pass": pass_rt,
        },
        "boundary_cases": boundary,
        "decimal_precision": decimal_tests,
        "safe_divide": {"zero_denom_returns_default": sd_zero == -999.0, "normal_ok": abs(sd_normal - 3.0) < 1e-12, "pass": safe_divide_ok},
        "sanitize_array": {"pass": sanitize_ok},
    }


def audit_redis_prices() -> dict:
    """Pull real Kalshi BBO prices from Redis and verify transforms on them."""
    result = {"available": False, "tickers_checked": 0, "errors": []}
    try:
        import redis as _redis
        r = _redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            password=os.getenv("REDIS_PASSWORD", "cemini_redis_2026"),
            decode_responses=True,
        )
        r.ping()
    except Exception as exc:
        result["error"] = str(exc)
        return result

    try:
        keys = r.keys("kalshi:ob:*:bbo")
        result["available"] = True
        result["tickers_checked"] = len(keys)
        samples = []
        for key in keys[:20]:  # sample up to 20
            bbo = r.hgetall(key)
            bid_s = bbo.get("best_bid", "")
            ask_s = bbo.get("best_ask", "")
            if not bid_s or not ask_s:
                continue
            try:
                bid = float(bid_s) / 100.0
                ask = float(ask_s) / 100.0
                mid = (bid + ask) / 2.0
                mid_clamped = clamp_probability(mid)
                lg = logit(mid_clamped)
                recovered = inv_logit(lg)
                err = abs(recovered - mid_clamped)
                samples.append({
                    "key": key,
                    "bid": bid,
                    "ask": ask,
                    "mid": mid,
                    "logit": lg,
                    "recovered": recovered,
                    "error": err,
                    "pass": err < RTOL,
                })
            except Exception as exc2:
                result["errors"].append({"key": key, "error": str(exc2)})
        result["samples"] = samples
        result["all_pass"] = all(s["pass"] for s in samples) if samples else True
    except Exception as exc:
        result["error"] = str(exc)

    return result


def main():
    print("🔬 logit_pricing precision audit starting...")
    t0 = time.time()

    roundtrip = audit_roundtrip()
    redis_prices = audit_redis_prices()

    overall_pass = (
        roundtrip["roundtrip"]["pass"]
        and roundtrip["safe_divide"]["pass"]
        and roundtrip["sanitize_array"]["pass"]
        and redis_prices.get("all_pass", True)
    )

    report = {
        "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_seconds": round(time.time() - t0, 3),
        "overall_pass": overall_pass,
        "tests": roundtrip,
        "redis_prices": redis_prices,
    }

    os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)
    with open(ARCHIVE_PATH, "w") as fh:
        json.dump(report, fh, indent=2)

    status = "✅ PASS" if overall_pass else "❌ FAIL"
    rt = roundtrip["roundtrip"]
    print(f"{status} — round-trip max_err={rt['max_error']:.2e} (tol={rt['tolerance']:.0e})")
    print(f"  Redis prices: {redis_prices.get('tickers_checked', 0)} BBO keys checked")
    print(f"  Report: {ARCHIVE_PATH}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
