from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.claim import ClaimModel
from backend.app.models.analysis import AnalysisModel
from backend.app.models.evidence import EvidenceModel
from backend.app.models.decision import DecisionModel
from backend.app.models.assessment import AssessmentModel
from backend.app.services.decision_service import DecisionService
from backend.app.services.assessment_service import AssessmentService
from backend.app.schemas.claim import ClaimResponse
from backend.app.schemas.assessment import DimensionScores
from backend.app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardProgressResponse,
    DashboardHistoryResponse
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.decision_service = DecisionService(db)
        self.assessment_service = AssessmentService(db)

    def get_overview(self, user_id: Optional[str] = None) -> DashboardOverviewResponse:
        claims_query = self.db.query(ClaimModel)
        decisions_query = self.db.query(DecisionModel)
        
        if user_id:
            claims_query = claims_query.filter(ClaimModel.user_id == user_id)
            decisions_query = decisions_query.filter(DecisionModel.user_id == user_id)

        total_claims = claims_query.count()
        total_decisions = decisions_query.count()
        
        # Calculate analyses for matching claims
        if user_id:
            total_analyses = self.db.query(AnalysisModel).join(ClaimModel).filter(ClaimModel.user_id == user_id).count()
        else:
            total_analyses = self.db.query(AnalysisModel).count()

        total_evidence = self.db.query(EvidenceModel).count()

        recent_claims = (
            claims_query
            .order_by(ClaimModel.submitted_at.desc())
            .limit(5)
            .all()
        )

        recent_decision_records = (
            decisions_query
            .order_by(DecisionModel.created_at.desc())
            .limit(5)
            .all()
        )
        recent_decisions = [self.decision_service._build_response(d) for d in recent_decision_records]

        return DashboardOverviewResponse(
            total_claims_submitted=total_claims,
            total_claims_analyzed=total_analyses,
            total_evidence_records=total_evidence,
            total_decisions_recorded=total_decisions,
            recent_claims=[ClaimResponse.model_validate(c) for c in recent_claims],
            recent_decisions=recent_decisions
        )

    def get_progress(self, session_id: str) -> DashboardProgressResponse:
        baseline = (
            self.db.query(AssessmentModel)
            .filter(AssessmentModel.session_id == session_id, AssessmentModel.assessment_stage == "BASELINE")
            .order_by(AssessmentModel.created_at.desc())
            .first()
        )
        transfer = (
            self.db.query(AssessmentModel)
            .filter(AssessmentModel.session_id == session_id, AssessmentModel.assessment_stage == "INDEPENDENT_TRANSFER")
            .order_by(AssessmentModel.created_at.desc())
            .first()
        )

        has_baseline = baseline is not None
        has_transfer = transfer is not None

        baseline_score = baseline.total_score if baseline else None
        transfer_score = transfer.total_score if transfer else None
        delta: Optional[float] = None
        dim_scores: Optional[DimensionScores] = None

        practice_count = (
            self.db.query(DecisionModel)
            .filter(DecisionModel.user_id == session_id)
            .count()
        )

        if has_baseline and has_transfer:
            delta = round(transfer.total_score - baseline.total_score, 1)
            status = "ASSESSMENT_COMPLETED"
            summary = (
                f"Evaluation ability shifted by {delta:+.1f} percentage points "
                f"from {baseline.total_score:.1f}/100 to {transfer.total_score:.1f}/100."
            )
            dim_scores = DimensionScores(
                evidence_evaluation=transfer.score_evidence_eval,
                claim_specificity=transfer.score_claim_specificity,
                risk_awareness=transfer.score_risk_awareness,
                assumption_awareness=transfer.score_assumption_awareness,
                confidence_calibration=transfer.score_confidence_calibration,
                invalidation_sensitivity=transfer.score_assumption_awareness,
                horizon_calibration=transfer.score_claim_specificity,
                provenance_rigor=transfer.score_evidence_eval,
                epistemic_calibration=transfer.score_confidence_calibration
            )
        elif has_baseline:
            if practice_count > 0:
                status = "PRACTICE_IN_PROGRESS"
                summary = f"Baseline established at {baseline.total_score:.1f}/100 with {practice_count} assisted practice decision(s) recorded. Ready for Stage 3 Independent Assessment."
            else:
                status = "BASELINE_COMPLETED"
                summary = f"Baseline established at {baseline.total_score:.1f}/100. Ready for assisted practice and independent transfer."
            dim_scores = DimensionScores(
                evidence_evaluation=baseline.score_evidence_eval,
                claim_specificity=baseline.score_claim_specificity,
                risk_awareness=baseline.score_risk_awareness,
                assumption_awareness=baseline.score_assumption_awareness,
                confidence_calibration=baseline.score_confidence_calibration,
                invalidation_sensitivity=baseline.score_assumption_awareness,
                horizon_calibration=baseline.score_claim_specificity,
                provenance_rigor=baseline.score_evidence_eval,
                epistemic_calibration=baseline.score_confidence_calibration
            )
        else:
            status = "NOT_STARTED"
            summary = "No assessment sessions recorded yet. Start with a baseline evaluation."

        return DashboardProgressResponse(
            session_id=session_id,
            has_baseline=has_baseline,
            has_independent_transfer=has_transfer,
            baseline_total_score=baseline_score,
            latest_transfer_score=transfer_score,
            percentage_point_delta=delta,
            dimension_breakdown=dim_scores,
            status=status,
            learning_progress_summary=summary,
            practice_decisions_count=practice_count,
            baseline_score=baseline_score,
            transfer_score=transfer_score,
            delta=delta,
            has_transfer=has_transfer
        )

    def get_history(self, session_id: str) -> DashboardHistoryResponse:
        timeline = self.assessment_service.get_session_history(session_id)
        return DashboardHistoryResponse(
            session_id=session_id,
            total_evaluations=len(timeline),
            evaluation_timeline=timeline
        )
