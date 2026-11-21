import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.claim import ClaimModel
from backend.app.models.decision import DecisionModel
from backend.app.models.assessment import AssessmentModel
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel
from backend.app.models.user import UserModel
from backend.app.integrations.ai_engine_adapter import AIEngineAdapter
from backend.app.utils.scoring import DeterministicRubricScorer


# ===========================================================================
# 1. Innovation Engines: Falsifiability & Interpretation Forks
# ===========================================================================

def test_falsifiability_compiler_preserves_nulls_and_scores_criteria():
    """Verifies FalsifiabilityCompiler evaluates concrete criteria and preserves unstated attributes without guessing."""
    from claim_extraction.schemas import ExtractedClaim, InvalidationCriteria, DirectionEnum, ConfidenceLanguageEnum
    from claim_extraction.compiler import FalsifiabilityCompiler

    # Unstated time horizon and target must remain None
    claim = ExtractedClaim(
        claim_id="falsify-test-1",
        claim_summary="Megawatt Grid Systems will double revenue rapidly",
        raw_statement_excerpt="Megawatt Grid Systems will double revenue rapidly",
        company_name="Megawatt Grid Systems",
        ticker="MGS",
        direction=DirectionEnum.BULLISH,
        time_horizon=None,
        target_metric=None,
        confidence_language=ConfidenceLanguageEnum.HYPERBOLIC,
        invalidation_criteria=[],
        is_falsifiable=False,
        falsifiability_score=0.0
    )

    is_falsifiable, score, criteria = FalsifiabilityCompiler.compile_falsifiability(claim)
    assert is_falsifiable is False
    assert score <= 0.20, "Hyperbolic claim without numbers or boundaries must receive low falsifiability score"

    # Testable claim with explicit invalidation criteria
    testable_claim = ExtractedClaim(
        claim_id="falsify-test-2",
        claim_summary="Infosys will achieve 15% YoY revenue growth in FY26",
        raw_statement_excerpt="Infosys will achieve 15% YoY revenue growth in FY26",
        company_name="Infosys Limited",
        ticker="INFY",
        direction=DirectionEnum.BULLISH,
        time_horizon="FY26",
        target_metric="15% YoY revenue growth",
        confidence_language=ConfidenceLanguageEnum.MODERATE,
        invalidation_criteria=[
            InvalidationCriteria(
                metric_or_trigger="Reported revenue growth falls below 10%",
                invalidation_threshold="< 10%",
                time_boundary="FY26 annual results",
                observable_source="Audited annual SEBI / SEC filing"
            )
        ],
        is_falsifiable=True,
        falsifiability_score=0.85
    )

    is_falsifiable_2, score_2, criteria_2 = FalsifiabilityCompiler.compile_falsifiability(testable_claim)
    assert is_falsifiable_2 is True
    assert score_2 >= 0.70
    assert len(criteria_2) == 1


def test_counterfactual_learning_engine_generates_unrevealed_practice_claims():
    """Verifies CounterfactualClaimGenerator creates clean practice claims with preserved pedagogical properties."""
    from interpretation.counterfactual import CounterfactualClaimGenerator

    generator = CounterfactualClaimGenerator()
    result = generator.generate_practice_claim(template_category="VAGUE_TIMEFRAME")

    assert result.practice_claim is not None
    assert result.practice_claim.is_synthetic is True
    assert result.practice_claim.provenance_label == "SYNTHETIC"
    assert result.practice_claim.synthetic_company_name in generator.SYNTHETIC_COMPANIES

    # Must contain NO answers or hints in user-facing claim text
    assert "rubric" not in result.practice_claim.claim_text.lower()
    assert "flaw" not in result.practice_claim.claim_text.lower()
    assert len(result.preserved_properties) >= 1
    assert result.preserved_properties[0].property_name == "TIMEFRAME_SPECIFICITY"


def test_decision_sensitivity_engine_disclaimer_and_unexplained_variance():
    """Verifies DecisionSensitivityEngine produces neutral explanations, behavioral disclaimers, and variance flags."""
    from interpretation.sensitivity import DecisionSensitivityEngine, DecisionSensitivityInput, DecisionRecord

    engine = DecisionSensitivityEngine()

    # Shift without written rationale -> unexplained variance flag
    data = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=4.5,
            hypothetical_allocation_pct=25.0,
            written_rationale="Initial strong conviction based on preliminary news."
        ),
        revised_decision=DecisionRecord(
            confidence_level=2.0,
            hypothetical_allocation_pct=5.0,
            written_rationale=None  # No revised explanation provided
        ),
        selected_interpretation_forks=[],
        relevant_evidence_observations=["Q2 report showed 8% margin decline."]
    )

    explanation = engine.explain_sensitivity(data)
    assert explanation.confidence_delta == -2.5
    assert explanation.allocation_delta_pct == -20.0
    assert explanation.unexplained_variance_flag is True
    assert "Allocation sensitivity is descriptive behavioral data" in explanation.behavioral_disclaimer
    assert explanation.provenance_label == "Deterministic Decision Sensitivity Analysis"


# ===========================================================================
# 2. Learning Evaluation: 5 Scoring Dimensions
# ===========================================================================

def test_deterministic_5_dimension_scoring_rigor():
    """Verifies all five scoring dimensions with objective anchors and transparent feedback."""
    # Test high-rigor submission
    scores, total, feedback = DeterministicRubricScorer.score_assessment(
        identified_evidence_types=["10-K statutory filing", "Audited financial statement"],
        distinguished_primary_sources=True,
        identified_missing_specificity=["Operating vs Gross margin definition", "Specific fiscal quarter deadline"],
        identified_risk_factors=["Raw material cost headwinds", "Customer concentration risk"],
        recognized_alternative_interpretations=True,
        stated_confidence=40.0,
        evidence_backing_level="MODERATE",
        confidence_justification="Confidence is calibrated at 40% because while demand is strong, supply bottlenecks and unanchored dates introduce material downside."
    )

    assert scores["evidence_evaluation"] >= 15.0
    assert scores["claim_specificity"] >= 8.0
    assert scores["risk_awareness"] >= 10.0
    assert scores["assumption_awareness"] == 20.0
    assert scores["confidence_calibration"] >= 14.0
    assert total >= 70.0
    assert "evidence_evaluation" in feedback
    assert "confidence_calibration" in feedback


# ===========================================================================
# 3. Complete End-to-End Integration Workflow
# ===========================================================================

def test_complete_end_to_end_user_lifecycle(client: TestClient):
    """
    End-to-End Workflow Verification:
    Registration -> Login -> Profile -> Claim Submission -> Decision -> Revision -> Assessment -> Progress & Overview
    """
    # 1. Register User
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Integration Analyst",
        "email": "e2e_analyst@fintrace.app",
        "password": "SecurePassword#2026!"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["token"]
    user_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify Profile /auth/me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "e2e_analyst@fintrace.app"

    # 3. Submit Claim
    claim_res = client.post("/api/v1/claims", headers=headers, json={
        "original_claim": "Wipro Limited will expand cloud software revenues by 18% in FY27.",
        "company_name": "Wipro Limited",
        "ticker": "WIPRO",
        "time_horizon": "FY27"
    })
    assert claim_res.status_code == 201
    claim_id = claim_res.json()["id"]

    # 4. Check Virtual Decision Lab Scenarios
    scenarios_res = client.get("/api/v1/decision-lab/scenarios", headers=headers)
    assert scenarios_res.status_code == 200
    scenarios = scenarios_res.json()
    assert len(scenarios) >= 1

    # 5. Record Initial Decision
    dec_res = client.post("/api/v1/decisions", headers=headers, json={
        "claim_id": claim_id,
        "initial_thesis": "Initial expectation of robust cloud expansion.",
        "initial_confidence": 75.0,
        "initial_allocation": 15.0,
        "assumptions_evaluated": ["Strong deal pipeline", "Stable IT budgets"]
    })
    assert dec_res.status_code == 201
    decision_id = dec_res.json()["id"]

    # 6. Revise Decision After Evidence
    rev_res = client.put(f"/api/v1/decisions/{decision_id}/revise", headers=headers, json={
        "revised_thesis": "Tempered conviction after noting enterprise IT budget delays.",
        "revised_confidence": 50.0,
        "revised_allocation": 8.0,
        "reason_for_change": "Disclosures show deal deferrals across discretionary tech spending.",
        "assumptions_evaluated": ["Deal deferral risk confirmed"]
    })
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert rev_data["revised_confidence"] == 50.0
    assert rev_data["sensitivity_summary"] is not None
    assert rev_data["sensitivity_summary"]["allocation_delta_points"] == -7.0

    # 7. Submit Baseline Assessment
    base_res = client.post("/api/v1/assessments", headers=headers, json={
        "session_id": user_id,
        "claim_id": claim_id,
        "assessment_stage": "BASELINE",
        "identified_evidence_types": ["Statutory filing"],
        "distinguished_primary_sources": True,
        "identified_missing_specificity": ["Operating margin breakdown"],
        "identified_risk_factors": ["Client budget delays"],
        "recognized_alternative_interpretations": True,
        "stated_confidence": 75.0,
        "evidence_backing_level": "MODERATE",
        "confidence_justification": "Initial baseline perspective."
    })
    assert base_res.status_code == 201
    assert base_res.json()["total_score"] > 0

    # 8. Submit Independent Transfer Assessment (Showing measured learning progress)
    transfer_res = client.post("/api/v1/assessments", headers=headers, json={
        "session_id": user_id,
        "claim_id": claim_id,
        "assessment_stage": "INDEPENDENT_TRANSFER",
        "identified_evidence_types": ["Audited financial statement", "SEC 20-F annual report"],
        "distinguished_primary_sources": True,
        "identified_missing_specificity": ["Constant currency vs reported metric", "Segmental margin detail"],
        "identified_risk_factors": ["Wage inflation headwind", "Client deferrals", "Macro deceleration"],
        "recognized_alternative_interpretations": True,
        "stated_confidence": 45.0,
        "evidence_backing_level": "MODERATE",
        "confidence_justification": "Calibrated confidence accounting for macro deceleration and wage headwinds."
    })
    assert transfer_res.status_code == 201

    # 9. Verify Comparison Between Baseline and Independent Transfer
    comp_res = client.get(f"/api/v1/assessments/compare/{user_id}", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "percentage_point_delta" in comp_data
    assert comp_data["baseline_score"] > 0
    assert comp_data["latest_transfer_score"] > 0

    # 10. Verify Dashboard Overview & Progress Reflects User Data
    overview_res = client.get("/api/v1/dashboard/overview", headers=headers)
    assert overview_res.status_code == 200
    overview_data = overview_res.json()
    assert overview_data["total_claims_submitted"] == 1
    assert overview_data["total_decisions_recorded"] == 1

    progress_res = client.get("/api/v1/dashboard/progress", headers=headers)
    assert progress_res.status_code == 200
    progress_data = progress_res.json()
    assert progress_data["status"] == "ASSESSMENT_COMPLETED"
    assert progress_data["has_baseline"] is True
    assert progress_data["has_independent_transfer"] is True
    assert progress_data["percentage_point_delta"] == comp_data["percentage_point_delta"]
