"""Tests verifying fixes for Phase 1 audit findings (H-2, M-1, M-2)."""

from datetime import datetime, timezone

import pytest

from claim_extraction.schemas import ConfidenceLanguageEnum, DirectionEnum, ExtractedClaim
from interpretation.schemas import ForkAnalysisResult, InterpretationFork
from validation.deterministic import DeterministicValidator
from validation.schemas import ValidationSeverity


def test_h2_fork_plausibility_weight_normalization():
    """Verify that ForkAnalysisResult normalizes plausibility weights when sum > 1.0 (Audit Item H-2)."""
    fork1 = InterpretationFork(
        fork_title="Scenario 1",
        scenario_description="Bullish automotive recovery",
        plausibility_weight=0.7,
        implied_direction=DirectionEnum.BULLISH,
        distinguishing_evidence_needed="Q3 Margin > 18%",
    )
    fork2 = InterpretationFork(
        fork_title="Scenario 2",
        scenario_description="Regulatory credit distortion",
        plausibility_weight=0.6,
        implied_direction=DirectionEnum.NEUTRAL,
        distinguishing_evidence_needed="Regulatory credit breakdown",
    )

    # Initial sum is 0.7 + 0.6 = 1.3 (> 1.0)
    result = ForkAnalysisResult(
        claim_id="claim-100",
        ambiguity_detected=True,
        ambiguity_reasons=["Ambiguity detected"],
        forks=[fork1, fork2],
    )

    # After validator, total weight must be <= 1.0
    total_weight = sum(f.plausibility_weight for f in result.forks)
    assert total_weight <= 1.0
    # Proportions: 0.7 / 1.3 ≈ 0.5385, 0.6 / 1.3 ≈ 0.4615
    assert 0.53 <= result.forks[0].plausibility_weight <= 0.55
    assert 0.45 <= result.forks[1].plausibility_weight <= 0.47


def test_m1_expanded_chronology_validation():
    """Verify expanded chronology validation with 2-digit years, fiscal/quarter notations, and ISO dates (Audit Item M-1)."""
    validator = DeterministicValidator()
    pub_date = datetime(2025, 6, 1, tzinfo=timezone.utc)

    # Valid future horizons:
    valid_horizons = ["FY26", "Q3 26", "by end of 2026", "2025-12-31", "'26"]
    for horizon in valid_horizons:
        claim = ExtractedClaim(
            company_name="Tesla, Inc.",
            claim_summary="Tesla will expand margins.",
            direction=DirectionEnum.BULLISH,
            time_horizon=horizon,
            confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
            is_falsifiable=True,
            falsifiability_score=0.8,
            invalidation_criteria=[],
            raw_statement_excerpt="Tesla will expand margins by " + horizon,
        )
        res = validator.validate_claim(claim, published_at=pub_date)
        assert res.chronology_verified is True, f"Failed for valid horizon: {horizon}"

    # Invalid past horizons (precedes 2025 publication):
    invalid_horizons = ["FY24", "Q4 23", "2024-05-10", "by 2023", "'24"]
    for horizon in invalid_horizons:
        claim = ExtractedClaim(
            company_name="Tesla, Inc.",
            claim_summary="Tesla will expand margins.",
            direction=DirectionEnum.BULLISH,
            time_horizon=horizon,
            confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
            is_falsifiable=True,
            falsifiability_score=0.8,
            invalidation_criteria=[],
            raw_statement_excerpt="Tesla will expand margins by " + horizon,
        )
        res = validator.validate_claim(claim, published_at=pub_date)
        assert res.chronology_verified is False, f"Should fail for past horizon: {horizon}"
        assert any(i.issue_code == "CHRONOLOGY_INVERSION" for i in res.issues)


def test_m2_number_word_equivalence_in_grounding():
    """Verify number words ('four hundred', 'ten', 'fifty') are recognized as grounded targets (Audit Item M-2)."""
    validator = DeterministicValidator()

    # Source has word "four hundred dollars", extracted target is "$400"
    claim = ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla price target reaches four hundred dollars.",
        direction=DirectionEnum.BULLISH,
        target_metric="$400",
        time_horizon="2026",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.8,
        invalidation_criteria=[],
        raw_statement_excerpt="Our price target for Tesla is four hundred dollars by 2026.",
    )
    res = validator.validate_claim(claim, raw_text="Our price target for Tesla is four hundred dollars by 2026.")
    assert res.null_preservation_verified is True
    assert not any(i.issue_code == "HALLUCINATED_NUMERIC_TARGET" for i in res.issues)

    # Hallucinated target: "$999" is not in text either as digits or as words
    claim_bad = ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla price target reaches $999.",
        direction=DirectionEnum.BULLISH,
        target_metric="$999",
        time_horizon="2026",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.8,
        invalidation_criteria=[],
        raw_statement_excerpt="Our price target for Tesla is four hundred dollars by 2026.",
    )
    res_bad = validator.validate_claim(claim_bad, raw_text="Our price target for Tesla is four hundred dollars by 2026.")
    assert res_bad.null_preservation_verified is False
    assert any(i.issue_code == "HALLUCINATED_NUMERIC_TARGET" for i in res_bad.issues)
