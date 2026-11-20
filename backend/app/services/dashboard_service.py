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

    def get_overview(self) -> DashboardOverviewResponse:
        total_claims = self.db.query(ClaimModel).count()
        total_analyses = self.db.query(AnalysisModel).count()
        total_evidence = self.db.query(EvidenceModel).count()
        total_decisions = self.db.query(DecisionModel).count()

        recent_claims = (
            self.db.query(ClaimModel)
            .order_by(ClaimModel.submitted_at.desc())
            .limit(5)
            .all()
        )

        recent_decision_records = (
            self.db.query(DecisionModel)
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
                confidence_calibration=transfer.score_confidence_calibration
            )
        elif has_baseline:
            status = "BASELINE_COMPLETED"
            summary = f"Baseline established at {baseline.total_score:.1f}/100. Ready for assisted practice and independent transfer."
            dim_scores = DimensionScores(
                evidence_evaluation=baseline.score_evidence_eval,
                claim_specificity=baseline.score_claim_specificity,
                risk_awareness=baseline.score_risk_awareness,
                assumption_awareness=baseline.score_assumption_awareness,
                confidence_calibration=baseline.score_confidence_calibration
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
            learning_progress_summary=summary
        )

    def get_history(self, session_id: str) -> DashboardHistoryResponse:
        timeline = self.assessment_service.get_session_history(session_id)
        return DashboardHistoryResponse(
            session_id=session_id,
            total_evaluations=len(timeline),
            evaluation_timeline=timeline
        )
