"""Tests for Counterfactual / Practice Claim Generator."""

import pytest
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    ExtractedClaim,
    InvalidationCriteria,
)
from interpretation.counterfactual import CounterfactualClaimGenerator
from validation.errors import CounterfactualGenerationError


@pytest.fixture
def generator():
    return CounterfactualClaimGenerator()


def test_preserves_vague_timeframe_challenge(generator):
    """Verify that a claim with target but missing timeframe produces a vague-timeframe practice claim."""
    source_claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="Tesla will reach $400",
        raw_statement_excerpt="Tesla will hit $400 soon.",
        target_metric="$400",
        time_horizon=None,  # Missing timeframe
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=False,
        falsifiability_score=0.2,
    )

    result = generator.generate_practice_claim(source_claim)
    assert result.practice_claim is not None
    assert result.practice_claim.is_synthetic is True
    assert result.practice_claim.provenance_label == "SYNTHETIC"
    assert result.source_claim_id == source_claim.claim_id

    # The practice claim text must NOT mention Tesla or $400
    assert "Tesla" not in result.practice_claim.claim_text
    assert "$400" not in result.practice_claim.claim_text

    # Preserved property should be timeframe specificity
    props = [p.property_name for p in result.preserved_properties]
    assert "TIMEFRAME_SPECIFICITY" in props


def test_preserves_missing_invalidation_challenge(generator):
    """Verify that a claim with target and timeframe but no invalidation produces missing-invalidation claim."""
    source_claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="Apple to $250 by Q4 2026",
        raw_statement_excerpt="Apple stock will reach $250 by Q4 2026.",
        target_metric="$250",
        time_horizon="Q4 2026",
        invalidation_criteria=[],  # Missing invalidation
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=False,
        falsifiability_score=0.3,
    )

    result = generator.generate_practice_claim(source_claim)
    props = [p.property_name for p in result.preserved_properties]
    assert "INVALIDATION_ABSENCE" in props
    assert "Apple" not in result.practice_claim.claim_text


def test_preserves_hyperbolic_challenge(generator):
    """Verify hyperbolic assertiveness triggers a persuasion/hyperbolic practice claim."""
    source_claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="Guaranteed rocket to the moon",
        raw_statement_excerpt="Guaranteed rocket to the moon!",
        confidence_language=ConfidenceLanguageEnum.HYPERBOLIC,
        is_falsifiable=False,
        falsifiability_score=0.05,
    )

    result = generator.generate_practice_claim(source_claim)
    props = [p.property_name for p in result.preserved_properties]
    assert "PERSUASION_AND_RISK" in props


def test_fo_style_practice_claim_generation(generator):
    """Verify explicit request for F&O category generates derivative practice claim."""
    result = generator.generate_practice_claim(template_category="FO_STYLE_CLAIM")
    assert "CE" in result.practice_claim.claim_text or "PE" in result.practice_claim.claim_text or "expiry" in result.practice_claim.claim_text
    assert result.practice_claim.provenance_label == "SYNTHETIC"


def test_user_facing_practice_claim_leaks_zero_answers_or_hints(generator):
    """CRITICAL INVARIANT: The user-facing PracticeClaim object must contain ONLY the raw claim text."""
    result = generator.generate_practice_claim()
    pc = result.practice_claim

    # User-facing claim must not contain rubric hints or answers
    assert "rubric" not in pc.claim_text.lower()
    assert "flaw" not in pc.claim_text.lower()
    assert "pedagogical" not in pc.claim_text.lower()
    assert "hint" not in pc.claim_text.lower()


def test_strictly_synthetic_company_names(generator):
    """Verify company names are strictly fictional, preventing confusion with real market entities."""
    for category in generator.CONTROLLED_TEMPLATES.keys():
        result = generator.generate_practice_claim(template_category=category)
        company = result.practice_claim.synthetic_company_name
        assert company in generator.SYNTHETIC_COMPANIES
        assert result.practice_claim.is_synthetic is True


def test_safe_handling_of_none_input(generator):
    """Verify generator produces a valid default practice claim when input claim is None."""
    result = generator.generate_practice_claim(claim=None)
    assert result is not None
    assert result.practice_claim.claim_text != ""
    assert result.source_claim_id is None


def test_invalid_category_raises_typed_error(generator):
    """Verify requesting an unsupported category raises CounterfactualGenerationError."""
    with pytest.raises(CounterfactualGenerationError) as exc_info:
        generator.generate_practice_claim(template_category="NON_EXISTENT_CATEGORY")
    assert "Unknown template category" in str(exc_info.value)
