from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.common import AssessmentStage


class AssessmentCreate(BaseModel):
    session_id: str = Field(..., min_length=3, description="User or session identifier")
    claim_id: str = Field(..., min_length=3)
    assessment_stage: AssessmentStage = Field(...)

    # User response inputs evaluated against the fixed rubric
    identified_evidence_types: List[str] = Field(default_factory=list)
    distinguished_primary_sources: bool = Field(...)
    identified_missing_specificity: List[str] = Field(default_factory=list)
    identified_risk_factors: List[str] = Field(default_factory=list)
    recognized_alternative_interpretations: bool = Field(...)
    stated_confidence: float = Field(..., ge=0.0, le=100.0)
    evidence_backing_level: str = Field(default="NONE")  # NONE, LOW, MODERATE, HIGH
    confidence_justification: Optional[str] = Field(
        default=None,
        description="Optional explanation justifying how evidence, uncertainty, and risks support the stated confidence"
    )
    raw_answers: Optional[Dict[str, Any]] = None


class DimensionScores(BaseModel):
    evidence_evaluation: float
    claim_specificity: float
    risk_awareness: float
    assumption_awareness: float
    confidence_calibration: float  # Conceptual: Confidence Justification & Epistemic Alignment
    invalidation_sensitivity: Optional[float] = None
    horizon_calibration: Optional[float] = None
    provenance_rigor: Optional[float] = None
    epistemic_calibration: Optional[float] = None


class AssessmentQuestionOption(BaseModel):
    id: str
    label: str
    description: Optional[str] = None


class AssessmentDimensionPrompt(BaseModel):
    id: str
    name: str
    description: str
    prompt: str
    type: str  # multi_select, boolean, slider, select, textarea
    options: Optional[List[AssessmentQuestionOption]] = None


class AssessmentPromptResponse(BaseModel):
    stage: AssessmentStage
    claim_id: str
    ticker: str
    company_name: str
    statement: str
    time_horizon: str
    source_context: str
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    guidance: str
    dimensions: List[AssessmentDimensionPrompt]


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    claim_id: str
    assessment_stage: str
    score_evidence_eval: float
    score_claim_specificity: float
    score_risk_awareness: float
    score_assumption_awareness: float
    score_confidence_calibration: float  # Conceptual: Confidence Justification & Epistemic Alignment
    total_score: float
    dimension_scores: DimensionScores
    rubric_feedback: Dict[str, str]
    created_at: datetime


class AssessmentComparisonResponse(BaseModel):
    session_id: str
    baseline_score: float
    latest_transfer_score: float
    percentage_point_delta: float
    dimension_deltas: Dict[str, float]
    comparison_summary: str
