"""Integration tests for the end-to-end pipeline, dual-model reviewer, and degraded modes."""

import asyncio
from datetime import datetime, timezone
import pytest
from claim_extraction.schemas import EvidenceItem, SourceTypeEnum
from engine_interface import ClaimExtractionInput, DualModelReviewInput
from facade import FinTraceAIEngine
from orchestration.reviewer import DualModelReviewer
from providers.mock_provider import MockProvider
from providers.schemas import ProviderRequest, ProviderStatus
from validation.errors import ProviderError, ProviderRateLimitError, ProviderTimeoutError


def test_end_to_end_mock_pipeline():
    """Verify that the end-to-end AI pipeline runs successfully across all stages."""
    async def run():
        primary = MockProvider(name="mock-primary")
        reviewer = MockProvider(name="mock-reviewer")
        engine = FinTraceAIEngine(primary_provider=primary, reviewer_provider=reviewer)

        evidence = [
            EvidenceItem(
                source_name="SEC 10-K",
                source_url="https://sec.gov/tsla-10k",
                source_type=SourceTypeEnum.SEC_FILING,
                text_content="Tesla reported automotive revenues and target metrics for $400 scaling.",
            )
        ]

        inp = ClaimExtractionInput(
            raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
            source_url="https://x.com/analyst/status/123",
            published_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
            retrieved_evidence=evidence,
        )

        result = await engine.analyze_end_to_end(inp)

        # 1. Extraction verified
        assert result.claim.company_name == "Tesla, Inc."
        assert result.claim.target_metric == "$400"
        assert result.claim.is_falsifiable is True

        # 2. Validation verified
        assert result.validation.is_valid is True
        assert result.validation.null_preservation_verified is True
        assert result.validation.chronology_verified is True

        # 3. Fork analysis verified
        assert len(result.fork_analysis.forks) > 0
        assert result.fork_analysis.forks[0].provenance_label == "AI-Generated Interpretation (Hypothesis)"

        # 4. Dual-model review verified
        assert result.dual_model_review is not None
        assert "Two-model agreement is not proof of factual correctness" in result.dual_model_review.consensus_warning

        # 5. Timing telemetry verified
        assert result.pipeline_duration_ms > 0.0

    asyncio.run(run())


def test_dual_model_disagreement_spawns_forks():
    """Verify that reviewer disagreement is flagged and uncertainty forks are spawned."""
    async def run():
        primary = MockProvider(name="mock-primary")
        reviewer = MockProvider(name="mock-reviewer", disagree_with_primary=True)

        engine = FinTraceAIEngine(primary_provider=primary, reviewer_provider=reviewer)

        inp = ClaimExtractionInput(
            raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling."
        )
        claim = await engine.extract_and_compile(inp)

        review_input = DualModelReviewInput(claim=claim)
        review_output = await engine.review_dual_model(review_input)

        assert review_output.is_concordant is False
        assert len(review_output.disagreement_reasons) > 0
        assert len(review_output.spawned_forks) > 0
        assert review_output.spawned_forks[0].provenance_label == "AI-Generated Interpretation (Hypothesis)"
        assert "Two-model agreement is not proof of factual correctness" in review_output.consensus_warning

    asyncio.run(run())


def test_degraded_single_provider_mode():
    """Verify that missing reviewer does NOT pretend dual-model review occurred."""
    async def run():
        primary = MockProvider(name="mock-primary")
        # No reviewer provided!
        engine = FinTraceAIEngine(primary_provider=primary, reviewer_provider=None)

        inp = ClaimExtractionInput(raw_text="Tesla will reach $400 by end of 2026.")
        claim = await engine.extract_and_compile(inp)

        review_input = DualModelReviewInput(claim=claim)
        review_output = await engine.review_dual_model(review_input)

        assert review_output.is_concordant is False
        assert "DEGRADED OPERATION" in review_output.reviewer_critique_notes
        assert "Reviewer unavailable" in review_output.disagreement_reasons[0]

    asyncio.run(run())


def test_provider_simulated_timeout():
    """Verify that provider timeouts raise ProviderTimeoutError."""
    async def run():
        timeout_provider = MockProvider(force_timeout=True)
        req = ProviderRequest(
            model_id="test",
            messages=[],
            timeout_seconds=0.001,
        )
        with pytest.raises(ProviderTimeoutError):
            await timeout_provider.generate_text(req)

    asyncio.run(run())


def test_provider_simulated_rate_limit():
    """Verify that provider rate limits raise ProviderRateLimitError and affect health."""
    async def run():
        rate_limit_provider = MockProvider(force_rate_limit=True)
        req = ProviderRequest(model_id="test", messages=[])
        with pytest.raises(ProviderRateLimitError):
            await rate_limit_provider.generate_text(req)

        status = await rate_limit_provider.health_check()
        assert status == ProviderStatus.RATE_LIMITED

    asyncio.run(run())
