"""
Cemini Financial Suite — Kill Switch (Circuit Breaker)

Monitors trading system health and triggers controlled shutdowns when
anomalies are detected.

Checks
------
PnL velocity     : rate-of-loss per minute exceeds threshold
Order rate       : order message count anomalously high in a window
Connectivity     : exchange API latency exceeds 500 ms
Price deviation  : execution price deviates significantly from fair value
Master kill      : instantly disable all trading and sever connections

Integration
-----------
Publishes to the existing ``emergency_stop`` Redis pub/sub channel
(same channel used by panic_button.py) so the EMS and Kalshi autopilot
both receive the signal and cancel all resting orders.

All Redis operations fail silently — the kill switch itself must never
raise an exception.
"""

import json
import logging
import os
import time
from collections import deque
from typing import Deque, Optional, Tuple

logger = logging.getLogger("playbook.kill_switch")

# ----- Redis helpers (mirrors intel_bus pattern) ---------------------------- #
try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    logger.warning("[KillSwitch] redis package not available — pub/sub disabled")


def _make_redis():
    """Return a sync Redis client using env-sourced connection params."""
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return _redis_lib.Redis(
        host=host, port=6379, password=password,
        decode_responses=True, socket_connect_timeout=2,
    )


# ----- constants ------------------------------------------------------------ #
PNL_VELOCITY_WINDOW = 60.0          # seconds over which PnL rate is computed
PNL_VELOCITY_THRESHOLD = -0.01      # -1 % NAV / minute triggers halt
ORDER_RATE_WINDOW = 10.0            # seconds
ORDER_RATE_MAX = 100                # messages per window before anomaly flag
LATENCY_THRESHOLD_MS = 500.0       # milliseconds
PRICE_DEVIATION_MAX = 0.02         # 2 % from fair value triggers halt


class KillSwitch:
    """
    Circuit breaker for the Cemini trading system.

    Maintains rolling windows for PnL and order-rate monitoring.
    On any trigger, publishes ``CANCEL_ALL`` to the ``emergency_stop``
    Redis channel and sets the internal ``triggered`` flag.

    Parameters
    ----------
    pnl_vel_threshold  : float  Rate-of-loss per minute (fraction of NAV).
                                Default -0.01 (−1 % / min).
    order_rate_max     : int    Max order messages per 10-second window.
    latency_threshold  : float  Max acceptable API latency in ms.
    price_dev_max      : float  Max price deviation from fair value (fraction).
    """

    def __init__(
        self,
        pnl_vel_threshold: float = PNL_VELOCITY_THRESHOLD,
        order_rate_max: int = ORDER_RATE_MAX,
        latency_threshold: float = LATENCY_THRESHOLD_MS,
        price_dev_max: float = PRICE_DEVIATION_MAX,
    ):
        self.pnl_vel_threshold = pnl_vel_threshold
        self.order_rate_max = order_rate_max
        self.latency_threshold = latency_threshold
        self.price_dev_max = price_dev_max

        self.triggered: bool = False
        self.trigger_reason: str = ""
        self.trigger_time: float = 0.0
        self._halted_strategies: set = set()

        # Rolling time-stamped deques for velocity calculations
        self._pnl_log: Deque[Tuple[float, float]] = deque(maxlen=1000)  # (ts, pnl_value)
        self._order_log: Deque[float] = deque(maxlen=5000)              # ts of each order msg

    # ---------------------------------------------------------------------- #
    # PnL velocity
    # ---------------------------------------------------------------------- #
    def record_pnl(self, pnl_value: float) -> None:
        """Record a P&L snapshot (dollar or NAV-fraction value)."""
        self._pnl_log.append((time.monotonic(), pnl_value))

    def check_pnl_velocity(self, nav: float = 1.0) -> Optional[str]:
        """
        Compute PnL rate over the trailing window.

        Returns a halt reason string if velocity breaches the threshold,
        else None.

        Parameters
        ----------
        nav : float
            Current Net Asset Value.  Used to convert the absolute PnL change
            to a fraction.  Defaults to 1.0 (treat pnl_value as a fraction).
        """
        now = time.monotonic()
        cutoff = now - PNL_VELOCITY_WINDOW

        window = [(ts, v) for ts, v in self._pnl_log if ts >= cutoff]
        if len(window) < 2:
            return None

        oldest_pnl = window[0][1]
        newest_pnl = window[-1][1]
        elapsed = max(window[-1][0] - window[0][0], 1.0)

        pnl_delta = newest_pnl - oldest_pnl
        velocity_per_min = (pnl_delta / nav) / (elapsed / 60.0)

        if velocity_per_min < self.pnl_vel_threshold:
            reason = (
                f"[KillSwitch] PnL velocity {velocity_per_min:.4f} NAV/min "
                f"< threshold {self.pnl_vel_threshold:.4f}"
            )
            logger.warning(reason)
            return reason
        return None

    # ---------------------------------------------------------------------- #
    # Order rate
    # ---------------------------------------------------------------------- #
    def record_order_message(self) -> None:
        """Record that one order message was sent/received now."""
        self._order_log.append(time.monotonic())

    def check_order_rate(self) -> Optional[str]:
        """
        Count order messages in the trailing ORDER_RATE_WINDOW seconds.

        Returns a halt reason if rate is anomalously high.
        """
        now = time.monotonic()
        cutoff = now - ORDER_RATE_WINDOW
        count = sum(1 for ts in self._order_log if ts >= cutoff)
        if count > self.order_rate_max:
            reason = (
                f"[KillSwitch] Order rate anomaly: {count} messages in "
                f"{ORDER_RATE_WINDOW:.0f}s (limit={self.order_rate_max})"
            )
            logger.warning(reason)
            return reason
        return None

    # ---------------------------------------------------------------------- #
    # Connectivity
    # ---------------------------------------------------------------------- #
    def check_connectivity(self, latency_ms: float) -> Optional[str]:
        """
        Check exchange API latency.

        Returns a halt reason if *latency_ms* exceeds the threshold.
        """
        if latency_ms > self.latency_threshold:
            reason = (
                f"[KillSwitch] API latency {latency_ms:.1f} ms "
                f"> threshold {self.latency_threshold:.0f} ms"
            )
            logger.warning(reason)
            return reason
        return None

    # ---------------------------------------------------------------------- #
    # Price deviation
    # ---------------------------------------------------------------------- #
    def check_price_deviation(self, exec_price: float, fair_value: float) -> Optional[str]:
        """
        Check that *exec_price* is within acceptable bounds of *fair_value*.

        Returns a halt reason if deviation exceeds the threshold.
        """
        if fair_value <= 0:
            return None
        deviation = abs(exec_price - fair_value) / fair_value
        if deviation > self.price_dev_max:
            reason = (
                f"[KillSwitch] Price deviation {deviation:.2%} "
                f"(exec={exec_price:.4f}, fair={fair_value:.4f}) "
                f"> max {self.price_dev_max:.2%}"
            )
            logger.warning(reason)
            return reason
        return None

    # ---------------------------------------------------------------------- #
    # Strategy-level halt
    # ---------------------------------------------------------------------- #
    def halt_strategy(self, strategy: str, reason: str) -> None:
        """
        Quarantine a specific strategy without triggering a full system halt.

        The strategy name is added to an internal set; the runner loop is
        responsible for checking ``is_strategy_halted()`` before routing
        signals from that strategy.
        """
        self._halted_strategies.add(strategy)
        logger.warning("[KillSwitch] Strategy '%s' halted: %s", strategy, reason)
        self._publish_to_redis({
            "event": "strategy_halted",
            "strategy": strategy,
            "reason": reason,
            "timestamp": time.time(),
        }, channel="playbook:kill_switch")

    def is_strategy_halted(self, strategy: str) -> bool:
        """Return True if *strategy* is currently quarantined."""
        return strategy in self._halted_strategies

    def resume_strategy(self, strategy: str) -> None:
        """Manually re-arm *strategy* after review."""
        self._halted_strategies.discard(strategy)
        logger.info("[KillSwitch] Strategy '%s' manually resumed", strategy)

    # ---------------------------------------------------------------------- #
    # Master kill
    # ---------------------------------------------------------------------- #
    def trigger(self, reason: str) -> None:
        """
        Activate the master kill switch.

        Actions
        -------
        1. Sets ``self.triggered = True`` and records reason + timestamp.
        2. Publishes ``CANCEL_ALL`` to the ``emergency_stop`` Redis channel
           (same as panic_button.py — the EMS will cancel all orders).
        3. Logs a critical message.

        This method is idempotent — calling it multiple times does not
        re-publish.
        """
        if self.triggered:
            return   # already fired

        self.triggered = True
        self.trigger_reason = reason
        self.trigger_time = time.time()
        logger.critical("[KillSwitch] MASTER KILL TRIGGERED: %s", reason)

        # Broadcast to EMS
        self._broadcast_emergency_stop(reason)

    def _broadcast_emergency_stop(self, reason: str) -> None:
        """Publish CANCEL_ALL to the emergency_stop Redis channel."""
        if not _REDIS_AVAILABLE:
            logger.warning("[KillSwitch] Redis unavailable — cannot broadcast emergency_stop")
            return
        try:
            r = _make_redis()
            r.publish("emergency_stop", "CANCEL_ALL")
            # Also publish structured event for diagnostics
            self._publish_to_redis({
                "event": "kill_switch_triggered",
                "reason": reason,
                "timestamp": self.trigger_time,
            }, channel="playbook:kill_switch", client=r)
            r.close()
            logger.info("[KillSwitch] emergency_stop broadcast sent")
        except Exception as exc:
            logger.error("[KillSwitch] Failed to publish emergency_stop: %s", exc)

    def _publish_to_redis(self, payload: dict, channel: str, client=None) -> None:
        """Publish *payload* as JSON to *channel*.  Fails silently."""
        if not _REDIS_AVAILABLE:
            return
        owned = client is None
        try:
            r = client or _make_redis()
            r.publish(channel, json.dumps(payload))
            if owned:
                r.close()
        except Exception as exc:
            logger.debug("[KillSwitch] Redis publish failed (%s): %s", channel, exc)

    # ---------------------------------------------------------------------- #
    # Convenience: run all checks in one call
    # ---------------------------------------------------------------------- #
    def run_all_checks(self, nav: float = 1.0) -> Optional[str]:
        """
        Run PnL-velocity and order-rate checks.

        If either check fires, the kill switch is triggered automatically.

        Returns
        -------
        str or None
            The first halt reason encountered, or None if all checks pass.
        """
        for check_fn in (
            lambda: self.check_pnl_velocity(nav),
            self.check_order_rate,
        ):
            reason = check_fn()
            if reason:
                self.trigger(reason)
                return reason
        return None

    def state_snapshot(self) -> dict:
        """Return a plain dict of current kill-switch state (for logging)."""
        return {
            "triggered": self.triggered,
            "trigger_reason": self.trigger_reason,
            "trigger_time": self.trigger_time,
            "halted_strategies": sorted(self._halted_strategies),
        }
