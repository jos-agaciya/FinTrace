from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.assessment import AssessmentCreate, AssessmentResponse, AssessmentComparisonResponse
from backend.app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def submit_assessment(assessment_in: AssessmentCreate, db: Session = Depends(get_db)):
    """Submit investor claim evaluation for rubric-based deterministic scoring."""
    service = AssessmentService(db)
    try:
        return service.submit_assessment(assessment_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history", response_model=List[AssessmentResponse])
def get_assessment_history(session_id: str = Query(..., description="User or session identifier"), db: Session = Depends(get_db)):
    """Retrieve full evaluation score history across stages for a session."""
    service = AssessmentService(db)
    return service.get_session_history(session_id)


@router.get("/compare/{session_id}", response_model=AssessmentComparisonResponse)
def compare_baseline_and_transfer(session_id: str, db: Session = Depends(get_db)):
    """Compare baseline and independent transfer scores using percentage-point delta."""
    service = AssessmentService(db)
    try:
        return service.compare_stages(session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment_by_id(assessment_id: str, db: Session = Depends(get_db)):
    """Retrieve an assessment by ID."""
    service = AssessmentService(db)
    res = service.get_assessment(assessment_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")
    return res
