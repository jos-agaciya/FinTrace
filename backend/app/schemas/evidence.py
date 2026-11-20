from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.common import EvidenceCategory, ProvenanceStatus


class EvidenceCreate(BaseModel):
    title: str = Field(..., min_length=3)
    document_title: Optional[str] = None
    publisher: str = Field(..., min_length=2)
    source_url: str = Field(..., min_length=5)
    publication_date: Optional[datetime] = None
    evidence_category: EvidenceCategory = Field(default=EvidenceCategory.COMPANY_DISCLOSURE)
    company_identifier: Optional[str] = None
    company_symbol: Optional[str] = None
    company_isin: Optional[str] = None
    source_jurisdiction: str = Field(default="IN", description="e.g. IN, US")
    exchange: str = Field(default="NSE", description="e.g. NSE, BSE, SEC")
    content_summary: str = Field(..., min_length=10)
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.REAL)
    raw_payload: Optional[str] = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    document_title: Optional[str] = None
    publisher: str
    source_url: str
    publication_date: Optional[datetime] = None
    retrieval_timestamp: datetime
    retrieved_at: Optional[datetime] = Field(default=None, alias="retrieval_timestamp")
    evidence_category: str
    company_identifier: Optional[str] = None
    company_symbol: Optional[str] = None
    company_isin: Optional[str] = None
    source_jurisdiction: str = "IN"
    exchange: str = "NSE"
    content_summary: str
    provenance_status: str
    raw_payload: Optional[str] = None
    created_at: datetime


class ClaimEvidenceAssociation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    evidence: EvidenceResponse
    relevance_score: float
    association_notes: Optional[str] = None


class ClaimEvidenceListResponse(BaseModel):
    claim_id: str
    total: int
    items: List[ClaimEvidenceAssociation]
