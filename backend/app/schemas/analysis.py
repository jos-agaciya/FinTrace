from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.common import ProviderStatus


class InterpretationForkCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    ambiguous_phrase: str = Field(..., min_length=2)
    assumptions: List[str] = Field(default_factory=list)
    information_required: str = Field(..., min_length=5)
    is_ai_generated: bool = Field(default=True)


class InterpretationForkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    title: str
    description: str
    ambiguous_phrase: str
    assumptions: str  # JSON list
    information_required: str
    is_ai_generated: bool
    created_at: datetime


class CategorizedStatements(BaseModel):
    SOURCE_FACT: List[str]
    AI_INTERPRETATION: List[str]
    USER_ASSUMPTION: List[str]
    UNRESOLVED_QUESTION: List[str]


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    primary_provider: str
    secondary_provider: str
    provider_status: str
    fallback_reason: Optional[str] = None
    falsifiability_score: float
    missing_fields: str
    testability_explanation: str
    categorized_statements: str
    validation_status: str
    validation_notes: Optional[str] = None
    primary_output_summary: Optional[str] = None
    secondary_output_summary: Optional[str] = None
    created_at: datetime


class AnalysisDetailedResponse(BaseModel):
    analysis: AnalysisResponse
    categorized_statements_parsed: CategorizedStatements
    missing_fields_list: List[str]
    interpretation_forks: List[InterpretationForkResponse]
