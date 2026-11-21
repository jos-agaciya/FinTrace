"""Unit tests for deterministic validation rules and evidence grounding."""

from datetime import datetime, timezone
import pytest
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    EvidenceItem,
    ExtractedClaim,
    InvalidationCriteria,
    SourceTypeEnum,
)
from interpretation.schemas import InterpretationFork
from validation.deterministic import DeterministicValidator
from validation.schemas import GroundingStatus, ValidationSeverity


@pytest.fixture
def validator() -> DeterministicValidator:
    return DeterministicValidator()


def test_validation_clean_pass(validator):
    """Verify that a well-formed claim with source grounding passes validation."""
    claim = ExtractedClaim(
        company_name="Tesla, Inc.",
        ticker="TSLA",
        direction=DirectionEnum.BULLISH,
        claim_summary="Tesla to reach $400 by 2026",
        raw_statement_excerpt="Tesla to reach $400 by 2026 driven by Robotaxi",
        target_metric="$400",
        time_horizon="by 2026",
        invalidation_criteria=[
            InvalidationCriteria(
                metric_or_trigger="Zero commercial deployments by Q4 2026"
            )
        ],
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.85,
    )

    published_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    res = validator.validate_claim(claim, published_at=published_at)

    assert res.is_valid is True
    assert res.validation_status == "PASSED"
    assert res.null_preservation_verified is True
    assert res.chronology_verified is True
    assert res.numeric_bounds_verified is True
    assert len(res.issues) == 0


def test_validation_hallucinated_numeric(validator):
    """Verify that extracting a number absent from raw text triggers a validation error."""
    claim = ExtractedClaim(
        company_name="Apple",
        ticker="AAPL",
        direction=DirectionEnum.BULLISH,
        claim_summary="Apple to hit $300",
        raw_statement_excerpt="Apple shares looking strong this quarter.",  # Note: 300 is NOT in excerpt!
        target_metric="$300",
        confidence_language=ConfidenceLanguageEnum.MODERATE,
        is_falsifiable=False,
        falsifiability_score=0.3,
    )

    res = validator.validate_claim(claim)
    assert res.is_valid is False
    assert res.validation_status == "FAILED"
    assert any(i.issue_code == "HALLUCINATED_NUMERIC_TARGET" for i in res.issues)


def test_validation_chronological_inversion(validator):
    """Verify that a time horizon preceding the publication date triggers an error."""
    claim = ExtractedClaim(
        company_name="Microsoft",
        ticker="MSFT",
        direction=DirectionEnum.BULLISH,
        claim_summary="MSFT target $500",
        raw_statement_excerpt="Target $500 by Dec 2022",
        target_metric="$500",
        time_horizon="by Dec 2022",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=False,
        falsifiability_score=0.2,
    )

    published_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    res = validator.validate_claim(claim, published_at=published_at)

    assert res.is_valid is False
    assert res.chronology_verified is False
    assert any(i.issue_code == "CHRONOLOGY_INVERSION" for i in res.issues)


def test_validation_negative_price_target(validator):
    """Verify negative stock price targets trigger an error."""
    claim = ExtractedClaim(
        company_name="XYZ Corp",
        direction=DirectionEnum.BEARISH,
        claim_summary="XYZ drop to -$50",
        raw_statement_excerpt="Drop to -$50",
        target_metric="-$50",
        confidence_language=ConfidenceLanguageEnum.MODERATE,
        is_falsifiable=False,
        falsifiability_score=0.1,
    )

    res = validator.validate_claim(claim)
    assert res.is_valid is False
    assert any(i.issue_code == "NEGATIVE_PRICE_TARGET" for i in res.issues)


def test_validation_falsifiability_contradiction(validator):
    """Verify claim marked falsifiable with empty invalidation list fails validation."""
    claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="Generic bullish thesis",
        raw_statement_excerpt="Generic bullish thesis",
        confidence_language=ConfidenceLanguageEnum.MODERATE,
        is_falsifiable=True,  # Contradiction: True with 0 criteria
        falsifiability_score=0.7,
        invalidation_criteria=[],
    )

    res = validator.validate_claim(claim)
    assert res.is_valid is False
    assert any(i.issue_code == "FALSIFIABILITY_CONTRADICTION" for i in res.issues)


def test_evidence_grounding_checks(validator):
    """Verify evidence grounding accurately distinguishes supported, contradicted, and insufficient evidence."""
    claim = ExtractedClaim(
        company_name="Tesla",
        ticker="TSLA",
        direction=DirectionEnum.BULLISH,
        claim_summary="Tesla automotive delivery growth of 20%",
        raw_statement_excerpt="Tesla delivery growth of 20%",
        target_metric="20%",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=False,
        falsifiability_score=0.3,
    )

    ev_supported = EvidenceItem(
        source_name="SEC 10-Q Filing",
        source_url="https://sec.gov/tsla-10q",
        source_type=SourceTypeEnum.SEC_FILING,
        text_content="Tesla reported automotive deliveries grew 20% year over year.",
    )

    ev_unrelated = EvidenceItem(
        source_name="Boeing Press Release",
        source_url="https://boeing.com/release",
        source_type=SourceTypeEnum.NEWS_ARTICLE,
        text_content="Boeing commercial aircraft deliveries increased.",
    )

    ev_contradicted = EvidenceItem(
        source_name="Automotive Industry Report",
        source_url="https://auto-report.com/news",
        source_type=SourceTypeEnum.RESEARCH_NOTE,
        text_content="Tesla experienced a significant decline in quarterly deliveries.",
    )

    res = validator.validate_claim(
        claim, evidence=[ev_supported, ev_unrelated, ev_contradicted]
    )

    statuses = [g.status for g in res.grounding_checks]
    assert GroundingStatus.SUPPORTED in statuses
    assert GroundingStatus.INSUFFICIENT_EVIDENCE in statuses
    assert GroundingStatus.CONTRADICTED in statuses

    # Crucial check: Unsupported statements must not be automatically assumed false
    insufficient = next(g for g in res.grounding_checks if g.source_name == "Boeing Press Release")
    assert insufficient.status == GroundingStatus.INSUFFICIENT_EVIDENCE


def test_interpretation_fork_validation(validator):
    """Verify validation of interpretation fork provenance and weights."""
    valid_fork = InterpretationFork(
        fork_title="Core Unit Margin Rebound",
        scenario_description="Unit margins expand driven by lithium deflation.",
        plausibility_weight=0.6,
        implied_direction=DirectionEnum.BULLISH,
        distinguishing_evidence_needed="SEC 10-Q Segment Breakdown",
    )
    issues = validator.validate_interpretation_fork(valid_fork)
    assert len(issues) == 0

    vague_fork = InterpretationFork(
        fork_title="Vague Fork",
        scenario_description="Description",
        plausibility_weight=0.5,
        implied_direction=DirectionEnum.NEUTRAL,
        distinguishing_evidence_needed="none",  # Too short
    )
    vague_issues = validator.validate_interpretation_fork(vague_fork)
    assert any(i.issue_code == "MISSING_DISTINGUISHING_CRITERIA" for i in vague_issues)
