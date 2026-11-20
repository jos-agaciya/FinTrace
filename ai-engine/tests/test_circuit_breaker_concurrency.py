"""Concurrency tests verifying atomic single-probe gating in CircuitBreaker HALF_OPEN state (Audit Item M-2)."""

import asyncio

import pytest

from fallback.circuit_breaker import CircuitBreaker, CircuitState
from validation.errors import CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_half_open_allows_only_single_concurrent_probe():
    """Verify that when HALF_OPEN, exactly one trial request enters and concurrent callers fast-fail."""
    cb = CircuitBreaker(provider_name="test-concurrent", failure_threshold=1, recovery_timeout_seconds=0.05)

    # 1. Trip circuit to OPEN
    async def failing():
        raise RuntimeError("Trip")

    with pytest.raises(RuntimeError):
        await cb.call(failing)
    assert cb.state == CircuitState.OPEN

    # 2. Wait for cooldown to transition OPEN -> HALF_OPEN
    await asyncio.sleep(0.08)
    assert cb.state == CircuitState.HALF_OPEN

    # 3. Launch 5 concurrent calls simultaneously
    in_flight_count = 0
    max_concurrent_in_probe = 0
    executed_probes = 0
    fast_failed_count = 0

    async def slow_probe(call_id: int):
        nonlocal in_flight_count, max_concurrent_in_probe, executed_probes
        in_flight_count += 1
        max_concurrent_in_probe = max(max_concurrent_in_probe, in_flight_count)
        # Hold in-flight for 100ms
        await asyncio.sleep(0.1)
        executed_probes += 1
        in_flight_count -= 1
        return f"probe-{call_id}-success"

    async def worker(call_id: int):
        nonlocal fast_failed_count
        try:
            return await cb.call(slow_probe, call_id)
        except CircuitBreakerOpenError as exc:
            fast_failed_count += 1
            assert exc.details.get("probe_in_flight") is True
            return "fast-failed"

    results = await asyncio.gather(*[worker(i) for i in range(5)])

    # Exactly 1 probe should have executed, exactly 4 should have fast-failed!
    assert executed_probes == 1
    assert max_concurrent_in_probe == 1, "More than 1 concurrent probe entered the provider!"
    assert fast_failed_count == 4
    assert cb.state == CircuitState.CLOSED  # Recovered on probe success


@pytest.mark.asyncio
async def test_half_open_probe_failure_re_trips_to_open_and_clears_gate():
    """Verify that when a trial probe fails, circuit re-trips to OPEN and clears the probe gate."""
    cb = CircuitBreaker(provider_name="test-fail-probe", failure_threshold=1, recovery_timeout_seconds=0.05)

    # Trip to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(lambda: (_ for _ in ()).throw(RuntimeError("Trip")))
    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.08)
    assert cb.state == CircuitState.HALF_OPEN

    async def failing_probe():
        await asyncio.sleep(0.05)
        raise RuntimeError("Probe failed")

    with pytest.raises(RuntimeError):
        await cb.call(failing_probe)

    assert cb.state == CircuitState.OPEN
    assert cb.probe_in_flight is False


@pytest.mark.asyncio
async def test_half_open_probe_cancellation_clears_gate():
    """Verify that if a trial probe task is cancelled, the probe gate is released in finally:."""
    cb = CircuitBreaker(provider_name="test-cancel-probe", failure_threshold=1, recovery_timeout_seconds=0.05)

    # Trip to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(lambda: (_ for _ in ()).throw(RuntimeError("Trip")))
    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.08)
    assert cb.state == CircuitState.HALF_OPEN

    async def long_probe():
        await asyncio.sleep(2.0)
        return "ok"

    # Start task and cancel it mid-flight
    task = asyncio.create_task(cb.call(long_probe))
    await asyncio.sleep(0.02)
    assert cb.probe_in_flight is True

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Probe in flight must be cleared even after cancellation!
    assert cb.probe_in_flight is False
    assert cb.can_execute() is True
