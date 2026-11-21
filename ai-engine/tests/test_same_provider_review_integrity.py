"""Regression tests for same-provider review integrity and failover detection (Audit Item H-2)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from claim_extraction.schemas import ConfidenceLanguageEnum, DirectionEnum, ExtractedClaim
from orchestration.reviewer import DualModelReviewer
from orchestration.schemas import DualModelReviewInput, DualModelReviewOutput
from providers.mock_provider import MockProvider
from providers.schemas import ProviderRequest, ProviderResponse, TokenUsage


def _make_test_claim(provider_name: str = "groq", model_id: str = "llama-3.3-70b-versatile") -> ExtractedClaim:
    return ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla will reach $400 by end of 2026.",
        direction=DirectionEnum.BULLISH,
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.85,
        invalidation_criteria=[],
        raw_statement_excerpt="Tesla will reach $400 by end of 2026.",
        metadata={
            "provider_name": provider_name,
            "model_id": model_id,
        },
    )


def _make_mock_review_output(is_concordant: bool = True) -> DualModelReviewOutput:
    claim = _make_test_claim()
    return DualModelReviewOutput(
        primary_claim=claim,
        reviewer_critique_notes="Model agreed with falsifiability parameters.",
        is_concordant=is_concordant,
    )


@pytest.mark.asyncio
async def test_distinct_provider_review_is_valid_and_independent():
    """Verify Groq extraction + Gemini review is classified as valid independent dual-model review."""
    claim = _make_test_claim(provider_name="groq", model_id="llama-3.3-70b-versatile")

    mock_reviewer = MagicMock()
    mock_reviewer.provider_name = "gemini"
    mock_reviewer.default_model = "gemini-1.5-flash"
    mock_reviewer.health_check = AsyncMock(return_value="HEALTHY")
    mock_reviewer.generate_structured = AsyncMock(
        return_value=(
            _make_mock_review_output(is_concordant=True),
            ProviderResponse(
                provider_name="gemini",
                model_id="gemini-1.5-flash",
                latency_ms=120.0,
            ),
        )
    )

    primary = MagicMock()
    primary.provider_name = "groq"

    reviewer = DualModelReviewer(primary_provider=primary, reviewer_provider=mock_reviewer)
    inp = DualModelReviewInput(claim=claim)
    result = await reviewer.review(inp)

    assert result.independent_review_valid is True
    assert result.review_mode == "INDEPENDENT_DUAL_MODEL"
    assert result.is_concordant is True
    assert result.extractor_provider == "groq"
    assert result.reviewer_provider == "gemini"
    assert "DEGRADED" not in result.reviewer_critique_notes


@pytest.mark.asyncio
async def test_same_provider_review_after_failover_is_flagged_degraded():
    """Verify Gemini extraction after failover + Gemini review is flagged as degraded same-provider review."""
    # Claim was extracted by Gemini (due to primary failover)
    claim = _make_test_claim(provider_name="gemini", model_id="gemini-1.5-flash")

    mock_reviewer = MagicMock()
    mock_reviewer.provider_name = "gemini"
    mock_reviewer.default_model = "gemini-1.5-flash"
    mock_reviewer.health_check = AsyncMock(return_value="HEALTHY")
    mock_reviewer.generate_structured = AsyncMock(
        return_value=(
            _make_mock_review_output(is_concordant=True),
            ProviderResponse(
                provider_name="gemini",
                model_id="gemini-1.5-flash",
                latency_ms=110.0,
            ),
        )
    )

    primary = MagicMock()
    primary.provider_name = "resilient(groq->gemini)"

    reviewer = DualModelReviewer(primary_provider=primary, reviewer_provider=mock_reviewer)
    inp = DualModelReviewInput(claim=claim)
    result = await reviewer.review(inp)

    # 1. Independent review is invalid
    assert result.independent_review_valid is False
    assert result.review_mode == "DEGRADED_SAME_PROVIDER"

    # 2. Agreement determination is preserved without false claim of independence
    assert result.is_concordant is True
    assert "DEGRADED SAME-PROVIDER SELF-REVIEW" in result.reviewer_critique_notes
    assert result.extractor_provider == "gemini"
    assert result.reviewer_provider == "gemini"


@pytest.mark.asyncio
async def test_reviewer_unavailable_flags_single_provider_degraded():
    """Verify missing reviewer is flagged as DEGRADED_SINGLE_PROVIDER."""
    claim = _make_test_claim(provider_name="groq")
    primary = MagicMock()
    primary.provider_name = "groq"

    # No reviewer configured
    reviewer = DualModelReviewer(primary_provider=primary, reviewer_provider=None)
    inp = DualModelReviewInput(claim=claim)
    result = await reviewer.review(inp)

    assert result.independent_review_valid is False
    assert result.review_mode == "DEGRADED_SINGLE_PROVIDER"
    assert result.is_concordant is False
    assert "DEGRADED OPERATION" in result.reviewer_critique_notes


@pytest.mark.asyncio
async def test_disagreement_preserved_during_same_provider_review():
    """Verify that when the same provider disagrees with itself, disagreement is faithfully recorded."""
    claim = _make_test_claim(provider_name="gemini")

    mock_reviewer = MagicMock()
    mock_reviewer.provider_name = "gemini"
    mock_reviewer.default_model = "gemini-1.5-flash"
    mock_reviewer.health_check = AsyncMock(return_value="HEALTHY")
    mock_reviewer.generate_structured = AsyncMock(
        return_value=(
            _make_mock_review_output(is_concordant=False),
            ProviderResponse(
                provider_name="gemini",
                model_id="gemini-1.5-flash",
                latency_ms=105.0,
            ),
        )
    )

    primary = MagicMock()
    primary.provider_name = "gemini"

    reviewer = DualModelReviewer(primary_provider=primary, reviewer_provider=mock_reviewer)
    inp = DualModelReviewInput(claim=claim)
    result = await reviewer.review(inp)

    assert result.independent_review_valid is False
    assert result.review_mode == "DEGRADED_SAME_PROVIDER"
    assert result.is_concordant is False
    assert "DEGRADED SAME-PROVIDER" in result.reviewer_critique_notes
