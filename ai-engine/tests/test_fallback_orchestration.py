"""Integration tests for FallbackManager and resilient dual-model orchestration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from claim_extraction.schemas import ConfidenceLanguageEnum, DirectionEnum, ExtractedClaim
from engine_interface import ClaimExtractionInput
from facade import FinTraceAIEngine
from fallback.circuit_breaker import CircuitState
from fallback.fallback_manager import FallbackManager
from providers.mock_provider import MockProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest, ProviderResponse, TokenUsage
from validation.errors import (
    AllProvidersFailedError,
    CircuitBreakerOpenError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


def _make_response(text: str, model: str) -> ProviderResponse:
    return ProviderResponse(
        provider_name="test-provider",
        model_id=model,
        raw_content=text,
        latency_ms=15.0,
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )


@pytest.mark.asyncio
async def test_fallback_manager_primary_success():
    """Verify primary provider is used when healthy without invoking secondary."""
    primary = MagicMock()
    primary.provider_name = "groq-mock"
    primary.generate_text = AsyncMock(return_value=_make_response("Primary OK", "groq-llama"))

    secondary = MagicMock()
    secondary.provider_name = "gemini-mock"
    secondary.generate_text = AsyncMock()

    manager = FallbackManager(primary_provider=primary, secondary_provider=secondary)
    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Hello")])

    resp = await manager.generate_text(req)
    assert resp.raw_text == "Primary OK"
    assert resp.raw_metadata["fallback_used"] is False
    assert resp.raw_metadata["degraded"] is False
    assert secondary.generate_text.called is False


@pytest.mark.asyncio
async def test_fallback_manager_failover_on_rate_limit():
    """Verify transparent failover from primary to secondary on 429 rate limit."""
    primary = MagicMock()
    primary.provider_name = "groq-mock"
    primary.generate_text = AsyncMock(
        side_effect=ProviderRateLimitError("Groq 429: rate limit exceeded")
    )

    secondary = MagicMock()
    secondary.provider_name = "gemini-mock"
    secondary.generate_text = AsyncMock(return_value=_make_response("Secondary OK", "gemini-flash"))

    manager = FallbackManager(primary_provider=primary, secondary_provider=secondary)
    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Hello")])

    resp = await manager.generate_text(req)
    assert resp.raw_text == "Secondary OK"
    assert resp.raw_metadata["fallback_used"] is True
    assert resp.raw_metadata["degraded"] is True
    assert resp.raw_metadata["primary_provider"] == "groq-mock"
    assert "rate limit" in resp.raw_metadata["primary_failure_reason"].lower()


@pytest.mark.asyncio
async def test_fallback_manager_failover_on_timeout():
    """Verify transparent failover from primary to secondary on timeout boundary."""
    primary = MagicMock()
    primary.provider_name = "groq-mock"
    primary.generate_text = AsyncMock(side_effect=ProviderTimeoutError("Primary timed out after 15s"))

    secondary = MagicMock()
    secondary.provider_name = "gemini-mock"
    secondary.generate_text = AsyncMock(return_value=_make_response("Secondary OK", "gemini-flash"))

    manager = FallbackManager(primary_provider=primary, secondary_provider=secondary)
    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Hello")])

    resp = await manager.generate_text(req)
    assert resp.raw_text == "Secondary OK"
    assert resp.raw_metadata["fallback_used"] is True
    assert resp.raw_metadata["degraded"] is True


@pytest.mark.asyncio
async def test_fallback_manager_structured_failover():
    """Verify structured generation failover preserves Pydantic schema parsing."""
    claim = ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Robotaxi deployment in 2026.",
        direction=DirectionEnum.BULLISH,
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.8,
        invalidation_criteria=[],
        raw_statement_excerpt="Robotaxi deployment in 2026.",
    )

    primary = MagicMock()
    primary.provider_name = "groq-mock"
    primary.generate_structured = AsyncMock(side_effect=ProviderRateLimitError("429"))

    secondary = MagicMock()
    secondary.provider_name = "gemini-mock"
    secondary.generate_structured = AsyncMock(
        return_value=(claim, _make_response("{}", "gemini-flash"))
    )

    manager = FallbackManager(primary_provider=primary, secondary_provider=secondary)
    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Extract")])

    parsed, resp = await manager.generate_structured(req, ExtractedClaim)
    assert parsed.company_name == "Tesla, Inc."
    assert resp.raw_metadata["fallback_used"] is True
    assert resp.raw_metadata["degraded"] is True


@pytest.mark.asyncio
async def test_fallback_manager_circuit_breaker_trips_and_skips_primary():
    """Verify primary circuit trips to OPEN after threshold, immediately fast-failing to secondary."""
    primary = MagicMock()
    primary.provider_name = "groq-mock"
    primary.generate_text = AsyncMock(side_effect=ProviderRateLimitError("429"))

    secondary = MagicMock()
    secondary.provider_name = "gemini-mock"
    secondary.generate_text = AsyncMock(return_value=_make_response("Secondary OK", "gemini-flash"))

    # Threshold of 2 failures
    manager = FallbackManager(
        primary_provider=primary,
        secondary_provider=secondary,
        failure_threshold=2,
        recovery_timeout_seconds=60.0,
    )
    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Call")])

    # First call fails primary -> secondary fulfills
    await manager.generate_text(req)
    assert manager.primary_circuit.state == CircuitState.CLOSED
    assert manager.primary_circuit.consecutive_failures == 1

    # Second call fails primary -> trips primary to OPEN
    await manager.generate_text(req)
    assert manager.primary_circuit.state == CircuitState.OPEN

    # Third call: primary circuit is OPEN, so primary.generate_text is NOT called again
    primary.generate_text.reset_mock()
    resp3 = await manager.generate_text(req)
    assert resp3.raw_text == "Secondary OK"
    # primary.generate_text should not even be attempted because circuit fast-fails!
    assert primary.generate_text.called is False


@pytest.mark.asyncio
async def test_fallback_manager_all_providers_failed():
    """Verify AllProvidersFailedError is raised with diagnostic context when all providers fail."""
    primary = MagicMock()
    primary.provider_name = "groq-mock"
    primary.generate_text = AsyncMock(side_effect=ProviderRateLimitError("Groq 429"))

    secondary = MagicMock()
    secondary.provider_name = "gemini-mock"
    secondary.generate_text = AsyncMock(side_effect=ProviderTimeoutError("Gemini timeout"))

    manager = FallbackManager(primary_provider=primary, secondary_provider=secondary)
    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Call")])

    with pytest.raises(AllProvidersFailedError) as exc_info:
        await manager.generate_text(req)

    err = exc_info.value
    assert "All AI providers failed" in str(err)
    assert "primary_provider" in err.details
    assert "secondary_provider" in err.details


@pytest.mark.asyncio
async def test_end_to_end_engine_with_fallback_manager():
    """Verify FinTraceAIEngine operates seamlessly with FallbackManager."""
    # Create healthy mock providers
    primary_mock = MockProvider(name="mock-primary")
    secondary_mock = MockProvider(name="mock-secondary")

    resilient_primary = FallbackManager(
        primary_provider=primary_mock,
        secondary_provider=secondary_mock,
    )

    engine = FinTraceAIEngine(
        primary_provider=resilient_primary,
        reviewer_provider=secondary_mock,
    )

    inp = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
    )

    result = await engine.analyze_end_to_end(inp)
    assert "Tesla" in result.claim.company_name
    assert result.claim.target_metric == "$400"
    assert result.validation.is_valid is True
    assert result.fork_analysis is not None
    assert result.dual_model_review is not None
