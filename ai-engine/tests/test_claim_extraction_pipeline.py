"""Unit tests for Claim Understanding, Falsifiability Compiler, and Claim Extractor."""

import asyncio
import pytest
from claim_extraction.compiler import FalsifiabilityCompiler
from claim_extraction.extractor import ClaimExtractor
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    ExtractedClaim,
    InvalidationCriteria,
)
from engine_interface import ClaimExtractionInput
from providers.mock_provider import MockProvider


def test_complete_claim_extraction():
    """Verify extraction of a complete claim with concrete criteria, targets, and horizon."""
    async def run():
        provider = MockProvider(name="mock-primary")
        extractor = ClaimExtractor(provider)

        inp = ClaimExtractionInput(
            raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
            source_url="https://x.com/analyst/status/123",
            author="AutoAnalyst",
        )

        claim = await extractor.extract_claim(inp)

        assert claim.company_name == "Tesla, Inc."
        assert claim.ticker == "TSLA"
        assert claim.target_metric == "$400"
        assert claim.time_horizon == "end of 2026"
        assert claim.direction == DirectionEnum.BULLISH
        assert claim.is_falsifiable is True
        assert claim.falsifiability_score >= 0.70
        assert len(claim.invalidation_criteria) > 0
        assert claim.invalidation_criteria[0].observable_source is not None

    asyncio.run(run())


def test_vague_claim_extraction_null_preservation():
    """Verify that vague hype claims maintain null targets and horizons, and get low falsifiability."""
    async def run():
        provider = MockProvider(name="mock-primary")
        extractor = ClaimExtractor(provider)

        inp = ClaimExtractionInput(
            raw_text="Tech stocks look set for a massive rally very soon!"
        )

        claim = await extractor.extract_claim(inp)

        assert claim.company_name is None
        assert claim.ticker is None
        assert claim.target_metric is None
        assert claim.time_horizon is None
        assert claim.entry_condition is None
        assert claim.exit_condition is None
        assert claim.is_falsifiable is False
        assert claim.falsifiability_score <= 0.20
        assert len(claim.invalidation_criteria) == 0

    asyncio.run(run())


def test_ambiguous_company_name_no_hallucinated_ticker():
    """Verify that an ambiguous company name does NOT guess a ticker if not stated."""
    async def run():
        provider = MockProvider(name="mock-primary")
        extractor = ClaimExtractor(provider)

        inp = ClaimExtractionInput(
            raw_text="Delta reports record summer travel demand across domestic routes."
        )

        claim = await extractor.extract_claim(inp)

        assert claim.company_name == "Delta"
        # Invariant: Ticker must NOT be assumed to be DAL unless stated
        assert claim.ticker is None
        assert claim.target_metric is None

    asyncio.run(run())


def test_falsifiability_compiler_scoring():
    """Verify FalsifiabilityCompiler scores based on concrete thresholds, horizons, and sources."""
    compiler = FalsifiabilityCompiler()

    # Highly falsifiable claim
    rigorous_claim = ExtractedClaim(
        company_name="Apple",
        ticker="AAPL",
        direction=DirectionEnum.BULLISH,
        claim_summary="Services revenue > $25B in Q4 2026",
        raw_statement_excerpt="Services revenue > $25B in Q4 2026",
        target_metric="$25B",
        time_horizon="Q4 2026",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.5,
        invalidation_criteria=[
            InvalidationCriteria(
                metric_or_trigger="Services revenue",
                invalidation_threshold="< $25B",
                time_boundary="Q4 2026",
                observable_source="Apple Form 10-K",
            )
        ],
    )

    is_falsifiable, score, criteria = compiler.compile_falsifiability(rigorous_claim)
    assert is_falsifiable is True
    assert score >= 0.80

    # Vague claim
    vague_claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="Massive rally to the moon soon",
        raw_statement_excerpt="Massive rally to the moon soon",
        confidence_language=ConfidenceLanguageEnum.HYPERBOLIC,
        is_falsifiable=False,
        falsifiability_score=0.2,
    )

    is_falsifiable, score, criteria = compiler.compile_falsifiability(vague_claim)
    assert is_falsifiable is False
    assert score <= 0.15
