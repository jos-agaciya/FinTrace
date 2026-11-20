"""Regression tests verifying provider and fallback telemetry survival across the pipeline (Audit Item H-3)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from claim_extraction.schemas import ConfidenceLanguageEnum, DirectionEnum, ExtractedClaim
from engine_interface import ClaimExtractionInput, FullPipelineAnalysisResult
from facade import FinTraceAIEngine
from fallback.fallback_manager import FallbackManager
from interpretation.schemas import ForkAnalysisResult
from orchestration.schemas import DualModelReviewOutput
from providers.mock_provider import MockProvider
from providers.schemas import ProviderRequest, ProviderResponse, TokenUsage
from validation.errors import ProviderRateLimitError


def _make_claim(provider: str = "mock-primary", model: str = "model-1"):
    return ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla will reach $400 by end of 2026.",
        direction=DirectionEnum.BULLISH,
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.85,
        invalidation_criteria=[],
        raw_statement_excerpt="Tesla will reach $400 by end of 2026.",
        metadata={"provider_name": provider, "model_id": model},
    )


def _make_response(provider: str, model: str, latency: float = 12.0) -> ProviderResponse:
    return ProviderResponse(
        provider_name=provider,
        model_id=model,
        raw_content="{}",
        latency_ms=latency,
        token_usage=TokenUsage(prompt_tokens=40, completion_tokens=50, total_tokens=90),
    )


@pytest.mark.asyncio
async def test_telemetry_survival_normal_execution():
    """Verify provider, model, latency, and status survive across the entire facade pipeline."""
    primary = MockProvider(name="mock-primary")
    reviewer = MockProvider(name="mock-reviewer")
    engine = FinTraceAIEngine(primary_provider=primary, reviewer_provider=reviewer)

    inp = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
    )

    result = await engine.analyze_end_to_end(inp)

    # 1. Extraction metadata survived on ExtractedClaim
    assert "provider_name" in result.claim.metadata
    assert result.claim.metadata["provider_name"] == "mock-primary"
    assert result.claim.metadata["fallback_used"] is False

    # 2. Fork analysis metadata survived
    assert result.fork_analysis.metadata is not None
    assert result.fork_analysis.metadata["provider_name"] == "mock-primary"

    # 3. Reviewer metadata survived on DualModelReviewOutput
    assert result.dual_model_review is not None
    assert result.dual_model_review.reviewer_provider == "mock-reviewer"
    assert result.dual_model_review.independent_review_valid is True

    # 4. Final facade summary exposes execution telemetry
    assert result.primary_provider == "mock-primary"
    assert result.fallback_used is False
    assert result.is_degraded is False
    assert result.pipeline_duration_ms > 0.0


@pytest.mark.asyncio
async def test_telemetry_survival_after_primary_failover():
    """Verify fallback telemetry is accurately exposed on FullPipelineAnalysisResult after failover."""
    claim = _make_claim(provider="gemini", model="gemini-3.5-flash")

    # Primary (Groq) fails with 429
    primary_groq = MagicMock()
    primary_groq.provider_name = "groq"
    primary_groq.generate_structured = AsyncMock(
        side_effect=ProviderRateLimitError("Groq 429: rate limit exceeded")
    )
    primary_groq.health_check = AsyncMock(return_value="HEALTHY")

    # Secondary (Gemini) fulfills extraction and fork analysis
    secondary_gemini = MagicMock()
    secondary_gemini.provider_name = "gemini"
    secondary_gemini.default_model = "gemini-3.5-flash"

    async def mock_gemini_structured(req, resp_model):
        if issubclass(resp_model, ForkAnalysisResult):
            forks = ForkAnalysisResult(claim_id="c-1", ambiguity_detected=False, forks=[])
            return forks, _make_response("gemini", "gemini-3.5-flash")
        return claim, _make_response("gemini", "gemini-3.5-flash")

    secondary_gemini.generate_structured = AsyncMock(side_effect=mock_gemini_structured)
    secondary_gemini.health_check = AsyncMock(return_value="HEALTHY")

    # Independent Reviewer is also Gemini
    reviewer_gemini = MagicMock()
    reviewer_gemini.provider_name = "gemini"
    reviewer_gemini.default_model = "gemini-3.5-flash"
    reviewer_gemini.health_check = AsyncMock(return_value="HEALTHY")
    rev_out = DualModelReviewOutput(
        primary_claim=claim,
        is_concordant=True,
    )
    reviewer_gemini.generate_structured = AsyncMock(
        return_value=(rev_out, _make_response("gemini", "gemini-3.5-flash"))
    )

    resilient_primary = FallbackManager(
        primary_provider=primary_groq,
        secondary_provider=secondary_gemini,
    )

    engine = FinTraceAIEngine(
        primary_provider=resilient_primary,
        reviewer_provider=reviewer_gemini,
    )

    inp = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
    )

    result = await engine.analyze_end_to_end(inp)

    # Actual executing provider must be reported, NOT configured provider
    assert result.primary_provider == "gemini"
    assert result.fallback_used is True
    assert result.is_degraded is True
    assert "rate limit" in result.primary_failure_reason.lower()

    # Reviewer detected same-provider review because both extraction and review were Gemini
    assert result.dual_model_review is not None
    assert result.dual_model_review.independent_review_valid is False
    assert result.dual_model_review.review_mode == "DEGRADED_SAME_PROVIDER"
