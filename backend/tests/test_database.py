import pytest
from backend.app.models.claim import ClaimModel, InterpretationForkModel
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel
from backend.app.models.decision import DecisionModel
from backend.app.models.assessment import AssessmentModel


def test_claim_model_preserves_null_fields(db_session):
    claim = ClaimModel(
        original_claim="XYZ Ltd. will rise 30% in two months. Strong fundamentals.",
        company_name="XYZ Ltd.",
        claim_direction="BULLISH",
        target_value=30.0,
        target_unit="%",
        time_horizon="two months",
        ticker=None,
        entry_condition=None,
        exit_condition=None,
        invalidation_condition=None,
        provenance_status="USER_PROVIDED"
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)

    assert claim.id is not None
    assert claim.ticker is None
    assert claim.entry_condition is None
    assert claim.exit_condition is None
    assert claim.invalidation_condition is None
    assert claim.company_name == "XYZ Ltd."
    assert claim.provenance_status == "USER_PROVIDED"


def test_relationships(db_session):
    claim = ClaimModel(
        original_claim="Test claim for relationship testing",
        provenance_status="SYNTHETIC"
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)

    fork = InterpretationForkModel(
        claim_id=claim.id,
        title="Short-term speculation",
        description="Assumes momentum driven rally",
        ambiguous_phrase="will rise",
        assumptions='["No macroeconomic headwind", "Q3 results positive"]',
        information_required="Management guidance and audit reports",
        is_ai_generated=True
    )
    db_session.add(fork)

    evidence = EvidenceModel(
        title="Q2 Financial Statement",
        publisher="NSE Disclosures",
        source_url="https://nseindia.com/disclosures/xyz_q2.pdf",
        evidence_category="COMPANY_DISCLOSURE",
        content_summary="Revenue up 5%, PAT flat.",
        provenance_status="REAL"
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    claim_evidence = ClaimEvidenceModel(
        claim_id=claim.id,
        evidence_id=evidence.id,
        relevance_score=0.9
    )
    db_session.add(claim_evidence)

    decision = DecisionModel(
        claim_id=claim.id,
        interpretation_id=fork.id,
        initial_thesis="Strong buy momentum",
        initial_confidence=80.0,
        initial_allocation=25.0
    )
    db_session.add(decision)

    assessment = AssessmentModel(
        session_id="test-session-123",
        claim_id=claim.id,
        assessment_stage="BASELINE",
        score_evidence_eval=12.0,
        score_claim_specificity=10.0,
        score_risk_awareness=8.0,
        score_assumption_awareness=14.0,
        score_confidence_calibration=12.0,
        total_score=56.0,
        user_responses='{"q1": "yes"}',
        rubric_feedback='{"feedback": "Good evidence identification"}'
    )
    db_session.add(assessment)
    db_session.commit()

    retrieved = db_session.query(ClaimModel).filter_by(id=claim.id).first()
    assert len(retrieved.interpretation_forks) == 1
    assert retrieved.interpretation_forks[0].title == "Short-term speculation"
    assert len(retrieved.evidence_associations) == 1
    assert retrieved.evidence_associations[0].evidence.publisher == "NSE Disclosures"
    assert len(retrieved.decisions) == 1
    assert retrieved.decisions[0].initial_confidence == 80.0
    assert len(retrieved.assessments) == 1
    assert retrieved.assessments[0].total_score == 56.0
