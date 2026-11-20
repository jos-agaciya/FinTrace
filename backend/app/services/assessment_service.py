import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.assessment import AssessmentModel
from backend.app.repositories.assessment_repository import AssessmentRepository
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.utils.scoring import DeterministicRubricScorer
from backend.app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    DimensionScores,
    AssessmentComparisonResponse
)


class AssessmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AssessmentRepository(db)
        self.claim_repo = ClaimRepository(db)

    def submit_assessment(self, assessment_in: AssessmentCreate) -> AssessmentResponse:
        claim = self.claim_repo.get_by_id(assessment_in.claim_id)
        if not claim:
            raise ValueError(f"Claim {assessment_in.claim_id} not found.")

        # Compute deterministic scores across all 5 dimensions
        dim_scores, total_score, feedback = DeterministicRubricScorer.score_assessment(
            identified_evidence_types=assessment_in.identified_evidence_types,
            distinguished_primary_sources=assessment_in.distinguished_primary_sources,
            identified_missing_specificity=assessment_in.identified_missing_specificity,
            identified_risk_factors=assessment_in.identified_risk_factors,
            recognized_alternative_interpretations=assessment_in.recognized_alternative_interpretations,
            stated_confidence=assessment_in.stated_confidence,
            evidence_backing_level=assessment_in.evidence_backing_level,
            confidence_justification=assessment_in.confidence_justification
        )

        user_responses_payload = {
            "identified_evidence_types": assessment_in.identified_evidence_types,
            "distinguished_primary_sources": assessment_in.distinguished_primary_sources,
            "identified_missing_specificity": assessment_in.identified_missing_specificity,
            "identified_risk_factors": assessment_in.identified_risk_factors,
            "recognized_alternative_interpretations": assessment_in.recognized_alternative_interpretations,
            "stated_confidence": assessment_in.stated_confidence,
            "evidence_backing_level": assessment_in.evidence_backing_level,
            "confidence_justification": assessment_in.confidence_justification,
            "raw_answers": assessment_in.raw_answers
        }

        assessment = AssessmentModel(
            session_id=assessment_in.session_id,
            claim_id=assessment_in.claim_id,
            assessment_stage=assessment_in.assessment_stage.value,
            score_evidence_eval=dim_scores["evidence_evaluation"],
            score_claim_specificity=dim_scores["claim_specificity"],
            score_risk_awareness=dim_scores["risk_awareness"],
            score_assumption_awareness=dim_scores["assumption_awareness"],
            score_confidence_calibration=dim_scores["confidence_calibration"],
            total_score=total_score,
            user_responses=json.dumps(user_responses_payload),
            rubric_feedback=json.dumps(feedback)
        )

        created = self.repository.create(assessment)
        return self._build_response(created)

    def get_assessment(self, assessment_id: str) -> Optional[AssessmentResponse]:
        assessment = self.repository.get_by_id(assessment_id)
        if not assessment:
            return None
        return self._build_response(assessment)

    def get_session_history(self, session_id: str) -> List[AssessmentResponse]:
        items = self.repository.get_by_session(session_id)
        return [self._build_response(a) for a in items]

    def compare_stages(self, session_id: str) -> AssessmentComparisonResponse:
        baseline = self.repository.get_latest_by_stage(session_id, "BASELINE")
        transfer = self.repository.get_latest_by_stage(session_id, "INDEPENDENT_TRANSFER")

        if not baseline or not transfer:
            raise ValueError(
                f"Both BASELINE and INDEPENDENT_TRANSFER assessments required for comparison. "
                f"Found baseline: {baseline is not None}, transfer: {transfer is not None}."
            )

        percentage_point_delta = round(transfer.total_score - baseline.total_score, 1)

        dim_deltas = {
            "evidence_evaluation": round(transfer.score_evidence_eval - baseline.score_evidence_eval, 1),
            "claim_specificity": round(transfer.score_claim_specificity - baseline.score_claim_specificity, 1),
            "risk_awareness": round(transfer.score_risk_awareness - baseline.score_risk_awareness, 1),
            "assumption_awareness": round(transfer.score_assumption_awareness - baseline.score_assumption_awareness, 1),
            "confidence_calibration": round(transfer.score_confidence_calibration - baseline.score_confidence_calibration, 1)
        }

        if percentage_point_delta > 0:
            summary = (
                f"Investor decision evaluation score increased by {percentage_point_delta} percentage points "
                f"from {baseline.total_score:.1f}/100 (baseline) to {transfer.total_score:.1f}/100 (independent transfer). "
                "Demonstrates improved analytical rigor and critical evaluation of financial claims without AI assistance."
            )
        elif percentage_point_delta < 0:
            summary = (
                f"Investor decision evaluation score decreased by {abs(percentage_point_delta)} percentage points "
                f"from {baseline.total_score:.1f}/100 to {transfer.total_score:.1f}/100."
            )
        else:
            summary = f"Investor decision evaluation score remained unchanged at {baseline.total_score:.1f}/100."

        return AssessmentComparisonResponse(
            session_id=session_id,
            baseline_score=baseline.total_score,
            latest_transfer_score=transfer.total_score,
            percentage_point_delta=percentage_point_delta,
            dimension_deltas=dim_deltas,
            comparison_summary=summary
        )

    def _build_response(self, a: AssessmentModel) -> AssessmentResponse:
        feedback = json.loads(a.rubric_feedback)
        dim_scores = DimensionScores(
            evidence_evaluation=a.score_evidence_eval,
            claim_specificity=a.score_claim_specificity,
            risk_awareness=a.score_risk_awareness,
            assumption_awareness=a.score_assumption_awareness,
            confidence_calibration=a.score_confidence_calibration
        )

        return AssessmentResponse(
            id=a.id,
            session_id=a.session_id,
            claim_id=a.claim_id,
            assessment_stage=a.assessment_stage,
            score_evidence_eval=a.score_evidence_eval,
            score_claim_specificity=a.score_claim_specificity,
            score_risk_awareness=a.score_risk_awareness,
            score_assumption_awareness=a.score_assumption_awareness,
            score_confidence_calibration=a.score_confidence_calibration,
            total_score=a.total_score,
            dimension_scores=dim_scores,
            rubric_feedback=feedback,
            created_at=a.created_at
        )
