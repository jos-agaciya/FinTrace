"""Comprehensive unit tests for the CircuitBreaker state machine."""

import asyncio
import time

import pytest

from fallback.circuit_breaker import CircuitBreaker, CircuitState
from validation.errors import CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state_success():
    """Verify circuit breaker stays CLOSED during successful operations."""
    cb = CircuitBreaker(provider_name="test-provider", failure_threshold=3, recovery_timeout_seconds=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    async def successful_call():
        return "success"

    result = await cb.call(successful_call)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 0
    assert cb.total_successes == 1


@pytest.mark.asyncio
async def test_circuit_breaker_trips_to_open_on_threshold():
    """Verify circuit breaker transitions CLOSED -> OPEN after consecutive failures reach threshold."""
    cb = CircuitBreaker(provider_name="test-provider", failure_threshold=2, recovery_timeout_seconds=1.0)

    async def failing_call():
        raise RuntimeError("Simulated provider outage")

    # First failure
    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 1

    # Second failure reaches threshold (2) -> Trips to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN
    assert cb.consecutive_failures == 2
    assert cb.can_execute() is False


@pytest.mark.asyncio
async def test_circuit_breaker_fast_fails_when_open():
    """Verify circuit breaker fast-fails immediately with CircuitBreakerOpenError when OPEN."""
    cb = CircuitBreaker(provider_name="test-provider", failure_threshold=1, recovery_timeout_seconds=5.0)

    async def failing_call():
        raise RuntimeError("Outage")

    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN

    # Subsequent call must fast-fail without running the inner function
    called = False

    async def should_not_run():
        nonlocal called
        called = True
        return "ok"

    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await cb.call(should_not_run)

    assert called is False
    assert "is OPEN" in str(exc_info.value)
    assert exc_info.value.details["provider_name"] == "test-provider"


@pytest.mark.asyncio
async def test_circuit_breaker_recovers_via_half_open():
    """Verify circuit breaker transitions OPEN -> HALF_OPEN after cooldown, and recovers to CLOSED on success."""
    # Use a tiny recovery timeout of 0.1s for test speed
    cb = CircuitBreaker(provider_name="test-provider", failure_threshold=1, recovery_timeout_seconds=0.1)

    async def failing_call():
        raise RuntimeError("Temporary error")

    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN

    # Sleep slightly past cooldown
    await asyncio.sleep(0.15)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.can_execute() is True

    # Trial request succeeds -> recovers to CLOSED
    async def successful_call():
        return "recovered"

    result = await cb.call(successful_call)
    assert result == "recovered"
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 0


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure_re_trips_to_open():
    """Verify that a failure during HALF_OPEN immediately re-trips the breaker to OPEN."""
    cb = CircuitBreaker(provider_name="test-provider", failure_threshold=1, recovery_timeout_seconds=0.1)

    async def failing_call():
        raise RuntimeError("Flapping error")

    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN

    # Wait for cooldown
    await asyncio.sleep(0.15)
    assert cb.state == CircuitState.HALF_OPEN

    # Trial request fails -> immediately trips back to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_diagnostics_and_reset():
    """Verify diagnostics dictionary and manual reset functionality."""
    cb = CircuitBreaker(provider_name="test-provider", failure_threshold=2, recovery_timeout_seconds=10.0)
    cb.record_failure("Test failure")
    diag = cb.get_diagnostics()

    assert diag["provider_name"] == "test-provider"
    assert diag["state"] == "CLOSED"
    assert diag["consecutive_failures"] == 1
    assert diag["total_failures"] == 1
    assert diag["last_failure_reason"] == "Test failure"

    # Trip and reset
    cb.record_failure("Second failure")
    assert cb.state == CircuitState.OPEN
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 0
