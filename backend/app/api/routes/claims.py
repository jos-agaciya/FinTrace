from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.claim import ClaimCreate, ClaimResponse, ClaimListResponse
from backend.app.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
def submit_claim(claim_in: ClaimCreate, db: Session = Depends(get_db)):
    """Submit a new financial claim for analysis."""
    service = ClaimService(db)
    return service.submit_claim(claim_in)


@router.get("", response_model=ClaimListResponse)
def list_claims(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve history of submitted claims."""
    service = ClaimService(db)
    items, total = service.list_claims(skip=skip, limit=limit)
    return ClaimListResponse(total=total, items=items)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve an individual claim by ID."""
    service = ClaimService(db)
    claim = service.get_claim(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with ID {claim_id} not found"
        )
    return claim


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim(claim_id: str, db: Session = Depends(get_db)):
    """Delete a user-submitted claim."""
    service = ClaimService(db)
    deleted = service.delete_claim(claim_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with ID {claim_id} not found"
        )
    return None
