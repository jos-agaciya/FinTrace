from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse,
    ClaimEvidenceListResponse
)
from backend.app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def create_evidence(evidence_in: EvidenceCreate, db: Session = Depends(get_db)):
    """Add a verified evidence record."""
    service = EvidenceService(db)
    return service.store_evidence(evidence_in)


@router.get("", response_model=List[EvidenceResponse])
def list_evidence(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List verified evidence disclosures with optional keyword search filter."""
    service = EvidenceService(db)
    return service.list_all(query_str=q, skip=skip, limit=limit)


@router.get("/{claim_id}", response_model=ClaimEvidenceListResponse)
def get_evidence_for_claim(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve all evidence associated with a claim."""
    service = EvidenceService(db)
    items = service.get_claim_evidence(claim_id)
    return ClaimEvidenceListResponse(
        claim_id=claim_id,
        total=len(items),
        items=items
    )


@router.get("/item/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_item(evidence_id: str, db: Session = Depends(get_db)):
    """Retrieve a single evidence record by ID."""
    service = EvidenceService(db)
    item = service.get_evidence_item(evidence_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found"
        )
    return item


@router.post("/{claim_id}/retrieve", response_model=ClaimEvidenceListResponse)
async def trigger_evidence_retrieval(claim_id: str, db: Session = Depends(get_db)):
    """Trigger automated verifiable disclosure retrieval for a claim."""
    service = EvidenceService(db)
    items = await service.retrieve_for_claim(claim_id)
    return ClaimEvidenceListResponse(
        claim_id=claim_id,
        total=len(items),
        items=items
    )
