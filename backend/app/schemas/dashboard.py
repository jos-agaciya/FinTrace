from typing import Optional, List, Dict
from pydantic import BaseModel
from backend.app.schemas.claim import ClaimResponse
from backend.app.schemas.decision import DecisionResponse
from backend.app.schemas.assessment import AssessmentResponse, DimensionScores


class DashboardOverviewResponse(BaseModel):
    total_claims_submitted: int
    total_claims_analyzed: int
    total_evidence_records: int
    total_decisions_recorded: int
    recent_claims: List[ClaimResponse]
    recent_decisions: List[DecisionResponse]


class DashboardProgressResponse(BaseModel):
    session_id: str
    has_baseline: bool
    has_independent_transfer: bool
    baseline_total_score: Optional[float] = None
    latest_transfer_score: Optional[float] = None
    percentage_point_delta: Optional[float] = None
    dimension_breakdown: Optional[DimensionScores] = None
    status: str  # NOT_STARTED, BASELINE_COMPLETED, PRACTICE_IN_PROGRESS, ASSESSMENT_COMPLETED
    learning_progress_summary: str


class DashboardHistoryResponse(BaseModel):
    session_id: str
    total_evaluations: int
    evaluation_timeline: List[AssessmentResponse]
