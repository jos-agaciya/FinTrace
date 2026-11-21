"""Unit tests for the Interpretation Fork Engine."""

import asyncio
import pytest
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    ExtractedClaim,
)
from engine_interface import ForkAnalysisInput
from interpretation.fork_engine import InterpretationForkEngine
from providers.mock_provider import MockProvider


def test_fork_engine_ambiguity_and_generation():
    """Verify that semantic ambiguity triggers fork generation with immutable provenance."""
    async def run():
        provider = MockProvider(name="mock-primary")
        fork_engine = InterpretationForkEngine(provider)

        claim = ExtractedClaim(
            company_name="Tesla",
            ticker="TSLA",
            direction=DirectionEnum.BULLISH,
            claim_summary="Tesla margin recovery soon",
            raw_statement_excerpt="Tesla margin recovery soon",
            target_metric=None,  # Ambiguous
            time_horizon=None,   # Ambiguous
            confidence_language=ConfidenceLanguageEnum.MODERATE,
            is_falsifiable=False,
            falsifiability_score=0.25,
        )

        inp = ForkAnalysisInput(claim=claim, max_forks=2)
        result = await fork_engine.analyze_forks(inp)

        assert result.ambiguity_detected is True
        assert len(result.ambiguity_reasons) > 0
        assert len(result.forks) <= 2

        for fork in result.forks:
            # Critical invariant: must be labelled strictly as AI-generated hypothesis
            assert fork.provenance_label == "AI-Generated Interpretation (Hypothesis)"
            assert fork.distinguishing_evidence_needed is not None
            assert len(fork.distinguishing_evidence_needed) > 5
            assert 0.0 <= fork.plausibility_weight <= 1.0

        assert len(result.distinguishing_data_checklist) > 0

    asyncio.run(run())
