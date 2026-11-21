from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import UserModel
from backend.app.api.deps import get_current_user_optional
from backend.app.schemas.common import AssessmentStage
from backend.app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentComparisonResponse,
    AssessmentPromptResponse
)
from backend.app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def submit_assessment(
    assessment_in: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Submit investor claim evaluation for rubric-based deterministic scoring."""
    if current_user and (not assessment_in.session_id or assessment_in.session_id in ["default", "default_session"]):
        assessment_in.session_id = current_user.id
    service = AssessmentService(db)
    try:
        return service.submit_assessment(assessment_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history", response_model=List[AssessmentResponse])
def get_assessment_history(
    session_id: Optional[str] = Query(None, description="User or session identifier"),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve full evaluation score history across stages for a session or authenticated user."""
    target_session = session_id or (current_user.id if current_user else "default_session")
    service = AssessmentService(db)
    return service.get_session_history(target_session)


@router.get("/compare/{session_id}", response_model=AssessmentComparisonResponse)
def compare_baseline_and_transfer(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Compare baseline and independent transfer scores using percentage-point delta."""
    target_session = session_id
    if target_session == "me" and current_user:
        target_session = current_user.id
    service = AssessmentService(db)
    try:
        return service.compare_stages(target_session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/prompt", response_model=AssessmentPromptResponse)
def get_assessment_prompt(
    stage: AssessmentStage = Query(AssessmentStage.BASELINE, description="Assessment stage (BASELINE or INDEPENDENT_TRANSFER)"),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve an unassisted claim and structured 5-dimension evaluation prompt for Baseline or Independent Transfer."""
    service = AssessmentService(db)
    user_id = current_user.id if current_user else None
    return service.get_assessment_prompt(stage, user_id=user_id)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment_by_id(assessment_id: str, db: Session = Depends(get_db)):
    """Retrieve an assessment by ID."""
    service = AssessmentService(db)
    res = service.get_assessment(assessment_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")
    return res
