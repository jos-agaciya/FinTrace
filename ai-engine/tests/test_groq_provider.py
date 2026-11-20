"""Unit tests for GroqProvider with mocked AsyncGroq client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from claim_extraction.schemas import DirectionEnum, ExtractedClaim
from providers.groq_provider import GroqProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest, ProviderStatus
from validation.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
)


def _make_mock_groq_completion(content: str, model: str = "llama-3.3-70b-versatile"):
    """Helper creating a mock Groq completion response."""
    choice = MagicMock()
    choice.message.content = content
    usage = MagicMock()
    usage.prompt_tokens = 45
    usage.completion_tokens = 60
    usage.total_tokens = 105
    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = usage
    completion.model = model
    completion.id = "groq-mock-123"
    return completion


@pytest.mark.asyncio
async def test_groq_provider_text_generation():
    """Verify standard text generation with token telemetry."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_mock_groq_completion("Tesla operating margins will improve.")
    )

    provider = GroqProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        model_id="llama-3.3-70b-versatile",
        messages=[LLMMessage(role=MessageRole.USER, content="Analyze TSLA margins.")],
    )

    resp = await provider.generate_text(req)
    assert resp.raw_text == "Tesla operating margins will improve."
    assert resp.model_identifier == "llama-3.3-70b-versatile"
    assert resp.token_usage.total_tokens == 105
    assert resp.latency_ms > 0.0


@pytest.mark.asyncio
async def test_groq_provider_structured_generation_success():
    """Verify structured JSON generation parses successfully into Pydantic ExtractedClaim."""
    valid_claim_json = """
    {
        "claim_id": "c-groq-1",
        "company_name": "Tesla, Inc.",
        "ticker": "TSLA",
        "claim_summary": "Tesla reaches $400 by end of 2026.",
        "direction": "BULLISH",
        "target_metric": "$400",
        "time_horizon": "2026",
        "confidence_language": "ASSERTIVE",
        "invalidation_criteria": [],
        "is_falsifiable": true,
        "falsifiability_score": 0.85,
        "raw_statement_excerpt": "TSLA reaches $400 by 2026."
    }
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_mock_groq_completion(valid_claim_json)
    )

    provider = GroqProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        model_id="llama-3.3-70b-versatile",
        messages=[LLMMessage(role=MessageRole.USER, content="Extract thesis.")],
    )

    claim, resp = await provider.generate_structured(req, ExtractedClaim)
    assert isinstance(claim, ExtractedClaim)
    assert claim.company_name == "Tesla, Inc."
    assert claim.target_metric == "$400"
    assert claim.direction == DirectionEnum.BULLISH


@pytest.mark.asyncio
async def test_groq_provider_rate_limit_mapping():
    """Verify Groq 429 rate limit errors map to ProviderRateLimitError."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("Rate limit reached for model llama-3.3-70b: 429 error")
    )

    provider = GroqProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Test rate limit")],
    )

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.generate_text(req)
    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_groq_provider_timeout_mapping():
    """Verify timeout boundaries map to ProviderTimeoutError."""
    mock_client = MagicMock()

    async def slow_create(*args, **kwargs):
        await asyncio.sleep(0.5)

    mock_client.chat.completions.create = slow_create

    # Request timeout set to 0.05s
    provider = GroqProvider(api_key="test-key", timeout_seconds=0.05, client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Test timeout")],
        timeout_seconds=0.05,
    )

    with pytest.raises(ProviderTimeoutError):
        await provider.generate_text(req)


@pytest.mark.asyncio
async def test_groq_provider_malformed_json_schema_validation_error():
    """Verify malformed JSON from model raises SchemaValidationError."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_mock_groq_completion("Not a valid JSON output")
    )

    provider = GroqProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Extract")],
    )

    with pytest.raises(SchemaValidationError):
        await provider.generate_structured(req, ExtractedClaim)


@pytest.mark.asyncio
async def test_groq_provider_missing_api_key_raises_auth_error():
    """Verify that calling without API key raises ProviderAuthenticationError."""
    provider = GroqProvider(api_key="", client=None)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Hello")],
    )

    with pytest.raises(ProviderAuthenticationError):
        await provider.generate_text(req)
