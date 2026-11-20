from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.common import ProvenanceStatus, ClaimDirection


class ClaimCreate(BaseModel):
    original_claim: str = Field(..., min_length=5, description="Unmodified financial claim text")
    source_url: Optional[str] = Field(default=None, description="Source URL where claim was observed")
    source_platform: Optional[str] = Field(default=None, description="e.g. Telegram, Twitter/X, Reddit, WhatsApp")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.USER_PROVIDED)

    # Optional pre-parsed or user-hinted fields (strictly None if not stated)
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    claim_direction: Optional[ClaimDirection] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    time_horizon: Optional[str] = None
    entry_condition: Optional[str] = None
    exit_condition: Optional[str] = None
    invalidation_condition: Optional[str] = None
    evidence_or_rationale: Optional[str] = None


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_claim: str
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    submitted_at: datetime
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    claim_direction: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    time_horizon: Optional[str] = None
    entry_condition: Optional[str] = None
    exit_condition: Optional[str] = None
    invalidation_condition: Optional[str] = None
    evidence_or_rationale: Optional[str] = None
    provenance_status: str
    is_ambiguous_entity: bool = False
    entity_ambiguity_notes: Optional[str] = None
    created_at: datetime


class ClaimListResponse(BaseModel):
    total: int
    items: List[ClaimResponse]
