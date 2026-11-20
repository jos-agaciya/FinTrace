"""Unit tests for GeminiProvider with mocked Google GenAI client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from claim_extraction.schemas import DirectionEnum, ExtractedClaim
from providers.gemini_provider import GeminiProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest
from validation.errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
)


def _make_mock_gemini_response(content: str, model_id: str = "gemini-2.5-flash"):
    """Helper creating a mock Gemini response."""
    resp = MagicMock()
    resp.text = content
    usage = MagicMock()
    usage.prompt_token_count = 50
    usage.candidates_token_count = 75
    usage.total_token_count = 125
    resp.usage_metadata = usage
    resp.response_id = "gemini-mock-456"
    return resp


@pytest.mark.asyncio
async def test_gemini_provider_text_generation():
    """Verify standard text generation with token telemetry."""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_make_mock_gemini_response("Tesla gross margins will face headwinds.")
    )

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        model_id="gemini-2.5-flash",
        messages=[LLMMessage(role=MessageRole.USER, content="Critique TSLA thesis.")],
    )

    resp = await provider.generate_text(req)
    assert resp.raw_text == "Tesla gross margins will face headwinds."
    assert resp.model_identifier == "gemini-2.5-flash"
    assert resp.token_usage.total_tokens == 125
    assert resp.latency_ms > 0.0


@pytest.mark.asyncio
async def test_gemini_provider_structured_generation_success():
    """Verify structured generation parses into Pydantic ExtractedClaim."""
    valid_claim_json = """
    {
        "claim_id": "c-gemini-1",
        "company_name": "Apple, Inc.",
        "ticker": "AAPL",
        "claim_summary": "Services revenue to exceed $100B in 2026.",
        "direction": "BULLISH",
        "target_metric": "$100B",
        "time_horizon": "2026",
        "confidence_language": "ASSERTIVE",
        "invalidation_criteria": [],
        "is_falsifiable": true,
        "falsifiability_score": 0.9,
        "raw_statement_excerpt": "AAPL Services revenue to exceed $100B in 2026."
    }
    """
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_make_mock_gemini_response(valid_claim_json)
    )

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        model_id="gemini-2.5-flash",
        messages=[LLMMessage(role=MessageRole.USER, content="Extract thesis.")],
    )

    claim, resp = await provider.generate_structured(req, ExtractedClaim)
    assert isinstance(claim, ExtractedClaim)
    assert claim.company_name == "Apple, Inc."
    assert claim.target_metric == "$100B"
    assert claim.direction == DirectionEnum.BULLISH


@pytest.mark.asyncio
async def test_gemini_provider_rate_limit_mapping():
    """Verify Gemini 429 / RESOURCE_EXHAUSTED errors map to ProviderRateLimitError."""
    mock_client = MagicMock()
    err = Exception("429 ResourceExhausted: Quota exceeded for quota metric 'GenerateContent'")
    setattr(err, "code", 429)
    mock_client.aio.models.generate_content = AsyncMock(side_effect=err)

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Test rate limit")],
    )

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.generate_text(req)
    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_provider_timeout_mapping():
    """Verify timeout boundaries map to ProviderTimeoutError."""
    mock_client = MagicMock()

    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(0.5)

    mock_client.aio.models.generate_content = slow_generate

    provider = GeminiProvider(api_key="test-key", timeout_seconds=0.05, client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Test timeout")],
        timeout_seconds=0.05,
    )

    with pytest.raises(ProviderTimeoutError):
        await provider.generate_text(req)


@pytest.mark.asyncio
async def test_gemini_provider_malformed_json_schema_validation_error():
    """Verify malformed JSON from model raises SchemaValidationError."""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_make_mock_gemini_response("Invalid json payload")
    )

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Extract")],
    )

    with pytest.raises(SchemaValidationError):
        await provider.generate_structured(req, ExtractedClaim)


@pytest.mark.asyncio
async def test_gemini_provider_missing_api_key_raises_auth_error():
    """Verify that calling without API key raises ProviderAuthenticationError."""
    provider = GeminiProvider(api_key="", client=None)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Hello")],
    )

    with pytest.raises(ProviderAuthenticationError):
        await provider.generate_text(req)
