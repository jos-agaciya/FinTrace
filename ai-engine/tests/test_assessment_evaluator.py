"""Tests for Independent Assessment Evaluation Support."""

import pytest
from assessment.evaluator import AssessmentEvaluator
from assessment.schemas import (
    AssessmentDimensionEnum,
    UserAssessmentInput,
)
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    ExtractedClaim,
    InvalidationCriteria,
)


@pytest.fixture
def evaluator():
    return AssessmentEvaluator()


@pytest.fixture
def vague_claim():
    return ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="XYZ will double soon",
        raw_statement_excerpt="XYZ will double soon. Buy before it's too late!",
        target_metric="double",
        time_horizon=None,  # Missing timeframe
        confidence_language=ConfidenceLanguageEnum.HYPERBOLIC,
        is_falsifiable=False,
        falsifiability_score=0.15,
        invalidation_criteria=[],  # Missing invalidation
    )


def test_evaluates_all_five_dimensions(evaluator, vague_claim):
    """Verify that every assessment result contains evaluations for all five FinTrace dimensions."""
    inp = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text=(
            "The statement provides no concrete timeframe ('soon' is unanchored). "
            "There are no SEC filings or revenue data cited to support this. "
            "Downside risk and stop losses are completely absent. "
            "The author assumes market expansion without addressing competitive threats."
        ),
        user_confidence=1.5,
    )

    result = evaluator.evaluate_assessment(inp)
    assert len(result.dimension_evaluations) == 5

    for dim in AssessmentDimensionEnum:
        assert dim in result.dimension_evaluations
        dim_eval = result.dimension_evaluations[dim]
        assert 0.0 <= dim_eval.score <= 20.0
        assert dim_eval.scoring_anchor != ""
        assert dim_eval.feedback != ""

    assert 0.0 <= result.total_suggested_score <= 100.0


def test_recognizes_identified_structural_flaws(evaluator, vague_claim):
    """Verify evaluator awards specificity points when user spots missing timeframe and stop loss."""
    inp = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text="There is no timeframe given for this claim and no stop loss or invalidation condition.",
        user_confidence=2.0,
    )

    result = evaluator.evaluate_assessment(inp)
    spec_eval = result.dimension_evaluations[AssessmentDimensionEnum.CLAIM_SPECIFICITY]
    assert spec_eval.score >= 14.0
    assert len(spec_eval.correctly_identified_issues) >= 1


def test_confidence_calibration_scoring(evaluator, vague_claim):
    """Verify confidence calibration appropriately rewards skepticism on vague claims."""
    # User A: Low confidence (1.5) on vague claim -> Well calibrated
    inp_a = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text="The claim is too vague and lacks evidence.",
        user_confidence=1.5,
    )
    res_a = evaluator.evaluate_assessment(inp_a)
    cal_a = res_a.dimension_evaluations[AssessmentDimensionEnum.CONFIDENCE_CALIBRATION]
    assert cal_a.score == 20.0
    assert "Well-Calibrated" in cal_a.scoring_anchor

    # User B: High confidence (5.0) on vague claim -> Overconfident / Miscalibrated
    inp_b = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text="I am confident this stock will rise.",
        user_confidence=5.0,
    )
    res_b = evaluator.evaluate_assessment(inp_b)
    cal_b = res_b.dimension_evaluations[AssessmentDimensionEnum.CONFIDENCE_CALIBRATION]
    assert cal_b.score <= 5.0
    assert "Overconfident" in cal_b.scoring_anchor


def test_handles_empty_or_whitespace_critique_safely(evaluator, vague_claim):
    """Verify empty critique returns baseline results without throwing exceptions."""
    inp = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text="   ",
        user_confidence=3.0,
    )

    result = evaluator.evaluate_assessment(inp)
    assert result.total_suggested_score <= 15.0
    assert "No written evaluation" in result.overall_feedback


def test_evidence_dimension_scoring(evaluator, vague_claim):
    """Verify evidence dimension rewards citing statutory filings or primary sources."""
    inp_strong = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text="We must review the SEC 10-K and quarterly balance sheet before validating revenue growth.",
        user_confidence=2.0,
    )
    res_strong = evaluator.evaluate_assessment(inp_strong)
    ev_strong = res_strong.dimension_evaluations[AssessmentDimensionEnum.EVIDENCE_EVALUATION]
    assert ev_strong.score == 20.0
    assert "Exemplary" in ev_strong.scoring_anchor


def test_does_not_penalize_contrasting_user_opinion(evaluator, vague_claim):
    """CRITICAL INVARIANT: Evaluator does not penalize a user merely because their conclusion differs from an AI reading."""
    # User takes a contrarian view with good structural critique
    inp = UserAssessmentInput(
        claim=vague_claim,
        user_critique_text=(
            "I disagree with the bullish thesis entirely. "
            "Without annual report verification and given the unstated downside risk, "
            "this looks like unsubstantiated market noise."
        ),
        user_confidence=1.0,
    )
    result = evaluator.evaluate_assessment(inp)
    assert result.total_suggested_score >= 60.0
