"""Production circuit breaker implementation for FinTrace AI Engine provider resilience.

CRITICAL INVARIANTS:
1. Strict 3-state state machine: CLOSED, OPEN, HALF_OPEN.
2. Fast-fails immediately when OPEN, preventing thundering herds and cascading latency.
3. Automatically transitions OPEN -> HALF_OPEN after recovery_timeout_seconds.
4. Successful execution in HALF_OPEN recovers the circuit to CLOSED.
5. Failed execution in HALF_OPEN immediately trips back to OPEN.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from enum import Enum
import logging
import time
from typing import Any, Callable, Dict, Optional

from validation.errors import CircuitBreakerOpenError

logger = logging.getLogger("fintrace.ai.circuit_breaker")


class CircuitState(str, Enum):
    """The three discrete states of a Circuit Breaker."""
    CLOSED = "CLOSED"          # Normal operation; requests pass through
    OPEN = "OPEN"              # Breaker tripped; requests fast-fail immediately
    HALF_OPEN = "HALF_OPEN"    # Recovery probe window; limited trial requests allowed


class CircuitBreaker:
    """Protects model providers against cascading timeouts, 429 rate limits, and outages."""

    def __init__(
        self,
        provider_name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 60.0,
    ):
        """Initialize the circuit breaker.

        Args:
            provider_name: Identifier for the provider (e.g. 'groq-primary', 'gemini-reviewer').
            failure_threshold: Consecutive failures needed to trip CLOSED -> OPEN.
            recovery_timeout_seconds: Seconds to stay in OPEN before testing HALF_OPEN.
        """
        self.provider_name = provider_name
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_timeout_seconds = max(0.01, recovery_timeout_seconds)

        self._state: CircuitState = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._total_failures: int = 0
        self._total_successes: int = 0
        self._opened_at: Optional[float] = None
        self._last_state_change: datetime = datetime.now(timezone.utc)
        self._last_failure_reason: Optional[str] = None
        self._probe_in_flight: bool = False
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current state of the circuit breaker, evaluating any elapsed cooldowns."""
        self._evaluate_state()
        return self._state

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    @property
    def total_failures(self) -> int:
        return self._total_failures

    @property
    def total_successes(self) -> int:
        return self._total_successes

    @property
    def probe_in_flight(self) -> bool:
        """True if a single trial recovery request is currently in flight in HALF_OPEN state."""
        return self._probe_in_flight

    def _evaluate_state(self) -> None:
        """Evaluate if an OPEN circuit has cooled down into HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.recovery_timeout_seconds:
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = datetime.now(timezone.utc)
                logger.info(
                    f"Circuit breaker [{self.provider_name}] cooldown elapsed ({elapsed:.1f}s >= "
                    f"{self.recovery_timeout_seconds}s). Transitioning OPEN -> HALF_OPEN."
                )

    def can_execute(self) -> bool:
        """Check whether a request is permitted to proceed."""
        self._evaluate_state()
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.HALF_OPEN:
            return not self._probe_in_flight
        return False

    def record_success(self) -> None:
        """Record a successful operation. Resets failures and recovers HALF_OPEN -> CLOSED."""
        self._evaluate_state()
        self._total_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                f"Circuit breaker [{self.provider_name}] trial succeeded in HALF_OPEN. "
                "Transitioning HALF_OPEN -> CLOSED. Circuit fully recovered."
            )
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            self._last_state_change = datetime.now(timezone.utc)
        elif self._state == CircuitState.CLOSED:
            # Clear any transient consecutive failures on success
            self._consecutive_failures = 0

    def record_failure(self, reason: Optional[str] = None) -> None:
        """Record a failed operation. Advances failure count and trips if threshold met."""
        self._evaluate_state()
        self._consecutive_failures += 1
        self._total_failures += 1
        self._last_failure_reason = reason or "Unknown failure"

        if self._state == CircuitState.HALF_OPEN:
            # Probe failed; immediately re-trip to OPEN
            logger.warning(
                f"Circuit breaker [{self.provider_name}] trial FAILED in HALF_OPEN. "
                f"Reason: {self._last_failure_reason}. Re-tripping to OPEN."
            )
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()
            self._last_state_change = datetime.now(timezone.utc)

        elif self._state == CircuitState.CLOSED:
            if self._consecutive_failures >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker [{self.provider_name}] reached failure threshold "
                    f"({self._consecutive_failures}/{self.failure_threshold}). "
                    f"Tripping CLOSED -> OPEN. Fast-failing for {self.recovery_timeout_seconds}s. "
                    f"Last reason: {self._last_failure_reason}"
                )
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._last_state_change = datetime.now(timezone.utc)

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute an async callable wrapped in circuit breaker safety checks with concurrency-safe probe gating."""
        is_probe = False
        async with self._lock:
            self._evaluate_state()
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - (self._opened_at or time.monotonic())
                remaining = max(0.0, self.recovery_timeout_seconds - elapsed)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker for provider '{self.provider_name}' is OPEN. "
                    f"Fast-failing request. Retry allowed in {remaining:.1f}s.",
                    details={
                        "provider_name": self.provider_name,
                        "state": self._state.value,
                        "remaining_cooldown_seconds": remaining,
                        "last_failure_reason": self._last_failure_reason,
                    },
                )

            if self._state == CircuitState.HALF_OPEN:
                if self._probe_in_flight:
                    # Concurrency safety (M-2): Reject concurrent calls while trial probe is in flight
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker for provider '{self.provider_name}' is HALF_OPEN and a trial recovery probe is currently in flight. "
                        f"Concurrent request fast-failed to protect downstream provider.",
                        details={
                            "provider_name": self.provider_name,
                            "state": self._state.value,
                            "probe_in_flight": True,
                        },
                    )
                # Gate this request as the sole active probe
                self._probe_in_flight = True
                is_probe = True

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self.record_success()
            return result
        except Exception as exc:
            async with self._lock:
                self.record_failure(reason=str(exc))
            raise
        finally:
            if is_probe:
                async with self._lock:
                    self._probe_in_flight = False

    def reset(self) -> None:
        """Manually force-reset the breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = None
        self._last_state_change = datetime.now(timezone.utc)
        self._last_failure_reason = None
        self._probe_in_flight = False
        logger.info(f"Circuit breaker [{self.provider_name}] manually reset to CLOSED.")

    def get_diagnostics(self) -> Dict[str, Any]:
        """Diagnostic state summary for observability and telemetry."""
        self._evaluate_state()
        remaining = 0.0
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = time.monotonic() - self._opened_at
            remaining = max(0.0, self.recovery_timeout_seconds - elapsed)

        return {
            "provider_name": self.provider_name,
            "state": self._state.value,
            "probe_in_flight": self._probe_in_flight,
            "consecutive_failures": self._consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
            "remaining_cooldown_seconds": round(remaining, 2),
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "last_state_change": self._last_state_change.isoformat(),
            "last_failure_reason": self._last_failure_reason,
        }
