"""Regression tests for interpretation fork semantics and ambiguity boundaries (Audit Item M-3)."""

import pytest

from claim_extraction.schemas import ConfidenceLanguageEnum, DirectionEnum, ExtractedClaim
from interpretation.fork_engine import InterpretationForkEngine
from interpretation.schemas import ForkAnalysisResult, InterpretationFork
from providers.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_fork_engine_on_ambiguous_claim():
    """Verify that ambiguous margin claims generate alternative metric readings labeled as hypotheses."""
    provider = MockProvider(name="mock-provider")
    fork_engine = InterpretationForkEngine(provider)

    # Claim has ambiguous metric: "margin will expand" without specifying gross vs operating
    claim = ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla margin will expand soon.",
        direction=DirectionEnum.BULLISH,
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=False,
        falsifiability_score=0.2,
        invalidation_criteria=[],
        raw_statement_excerpt="Tesla margin will expand soon.",
    )

    result = await fork_engine.analyze_forks(claim)

    assert result.ambiguity_detected is True
    assert len(result.ambiguity_reasons) > 0
    # Must identify unanchored horizon and unspecified margin
    assert any("margin" in r.lower() for r in result.ambiguity_reasons)
    assert any("temporal" in r.lower() or "soon" in r.lower() for r in result.ambiguity_reasons)

    # Forks must be hypotheses
    for fork in result.forks:
        assert fork.provenance_label == "AI-Generated Interpretation (Hypothesis)"
        assert len(fork.distinguishing_evidence_needed) > 0

    # Total plausibility weight must satisfy <= 1.0
    total_w = sum(f.plausibility_weight for f in result.forks)
    assert total_w <= 1.0 + 1e-6


@pytest.mark.asyncio
async def test_fork_engine_telemetry_survival():
    """Verify that provider telemetry survives on ForkAnalysisResult."""
    provider = MockProvider(name="mock-provider")
    fork_engine = InterpretationForkEngine(provider)

    claim = ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
        direction=DirectionEnum.BULLISH,
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.85,
        invalidation_criteria=[],
        raw_statement_excerpt="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
    )

    result = await fork_engine.analyze_forks(claim)

    assert result.metadata is not None
    assert result.metadata.get("provider_name") == "mock-provider"
    assert "latency_ms" in result.metadata
