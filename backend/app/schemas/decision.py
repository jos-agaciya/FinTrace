from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DecisionCreate(BaseModel):
    claim_id: str
    interpretation_id: Optional[str] = None
    initial_thesis: str = Field(..., min_length=5, description="Initial reasoning thesis before counter-evidence")
    initial_confidence: float = Field(..., ge=0.0, le=100.0, description="Initial confidence 0-100%")
    initial_allocation: float = Field(..., ge=0.0, le=100.0, description="Hypothetical portfolio allocation %")
    assumptions_evaluated: Optional[List[str]] = Field(default_factory=list)


class DecisionRevise(BaseModel):
    revised_thesis: str = Field(..., min_length=5, description="Revised reasoning after reviewing forks and evidence")
    revised_confidence: float = Field(..., ge=0.0, le=100.0, description="Revised confidence 0-100%")
    revised_allocation: float = Field(..., ge=0.0, le=100.0, description="Revised portfolio allocation %")
    reason_for_change: str = Field(..., min_length=5, description="Explanation of why reasoning changed or was retained")
    assumptions_evaluated: Optional[List[str]] = None


class DecisionSensitivitySummary(BaseModel):
    confidence_delta_points: float
    allocation_delta_points: float
    reasoning_shift_type: str  # REDUCED_EXPOSURE, INCREASED_EXPOSURE, UNCHANGED, CONVICTION_SHIFT
    shift_explanation: str


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    interpretation_id: Optional[str] = None
    initial_thesis: str
    initial_confidence: float
    initial_allocation: float
    revised_thesis: Optional[str] = None
    revised_confidence: Optional[float] = None
    revised_allocation: Optional[float] = None
    reason_for_change: Optional[str] = None
    assumptions_evaluated: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sensitivity_summary: Optional[DecisionSensitivitySummary] = None
