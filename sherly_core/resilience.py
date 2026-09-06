"""
RESILIENCE & FAULT TOLERANCE — sherly_core/resilience.py
Implements operation-aware retries with exponential backoff and randomized jitter,
scoped circuit breakers, and bounded timeouts.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# 1. Scoped Circuit Breaker
# ---------------------------------------------------------------------------

class CircuitState(str, Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Failing; requests immediately rejected/diverted
    HALF_OPEN = "HALF_OPEN" # Testing recovery with a single probe request


class CircuitBreaker:
    """Protects a specific provider/operation scope from cascading failures."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 10.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_state_change = time.time()
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            now = time.time()
            if self.state == CircuitState.OPEN:
                if now - self.last_state_change > self.cooldown_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self.consecutive_failures = 0
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()

    def record_failure(self) -> None:
        with self._lock:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()


_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_circuit_breaker(scope: str) -> CircuitBreaker:
    """Retrieve or create a circuit breaker scoped to a provider:operation pair."""
    with _breakers_lock:
        if scope not in _breakers:
            _breakers[scope] = CircuitBreaker(scope)
        return _breakers[scope]


# ---------------------------------------------------------------------------
# 2. Operation-Aware Retry Policy
# ---------------------------------------------------------------------------

# Operations that are strictly non-idempotent or state-mutating (DO NOT RETRY BLINDLY)
_NON_RETRYABLE_OPERATIONS: set[str] = {
    "filesystem.write",
    "filesystem.delete",
    "terminal.execute",
    "action.approve",
    "action.apply",
}


def is_retryable_operation(operation_name: str) -> bool:
    """Verify whether an operation is idempotent and safe for transient retries."""
    return operation_name.lower() not in _NON_RETRYABLE_OPERATIONS


def retry_with_backoff(
    func: Callable[[], Any],
    operation_name: str = "read_operation",
    max_retries: int = 2,
    base_delay: float = 0.2,
    max_delay: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type, ...] = (Exception,),
) -> Any:
    """
    Executes func with exponential backoff + jitter for transient failures.
    Strictly refuses to retry non-idempotent/mutation operations.
    """
    if not is_retryable_operation(operation_name):
        return func()

    attempt = 0
    last_exception = None

    while attempt <= max_retries:
        try:
            return func()
        except retryable_exceptions as exc:
            last_exception = exc
            attempt += 1
            if attempt > max_retries:
                break

            # Calculate backoff delay with jitter
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)

            time.sleep(delay)

    raise last_exception or RuntimeError(f"Failed {operation_name} after {max_retries} retries")
