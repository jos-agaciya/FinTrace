from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.decision import DecisionCreate, DecisionRevise, DecisionResponse
from backend.app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["Decisions"])


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
def record_initial_decision(decision_in: DecisionCreate, db: Session = Depends(get_db)):
    """Record an initial hypothetical decision in the Virtual Decision Lab."""
    service = DecisionService(db)
    try:
        return service.record_initial_decision(decision_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{decision_id}/revise", response_model=DecisionResponse)
def record_decision_revision(decision_id: str, revision_in: DecisionRevise, db: Session = Depends(get_db)):
    """Record revised reasoning after reviewing evidence and interpretation forks."""
    service = DecisionService(db)
    try:
        return service.record_revision(decision_id, revision_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{claim_id}", response_model=List[DecisionResponse])
def get_decisions_for_claim(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve decision records and sensitivity analysis for a claim."""
    service = DecisionService(db)
    return service.get_decisions_for_claim(claim_id)
