from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import UserModel
from backend.app.api.deps import get_current_user_optional
from backend.app.schemas.decision import (
    DecisionCreate,
    DecisionRevise,
    DecisionResponse,
    DecisionCalibrationRequest,
    DecisionCalibrationResponse
)
from backend.app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["Decisions"])
lab_router = APIRouter(tags=["Virtual Decision Lab"])


def _calculate_calibration(data: DecisionCalibrationRequest) -> DecisionCalibrationResponse:
    delta = round(data.revisedConfidence - data.initialConfidence, 1)
    stance_changed = (data.initialStance or "").strip().lower() != (data.revisedStance or "").strip().lower()

    # Epistemic calibration score: rewards updating beliefs in response to evidence
    base_score = 75.0
    if stance_changed:
        base_score += 15.0
    if delta < 0:
        base_score += 10.0
    refuted_count = len([k for k, v in (data.refutedAssumptions or {}).items() if v])
    if refuted_count > 0:
        base_score += min(refuted_count * 5.0, 15.0)

    score = min(round(base_score, 1), 100.0)
    insights = (
        f"Confidence revised by {delta:+.1f} points after reviewing "
        f"{refuted_count} evidence item(s). Epistemic stance successfully calibrated."
    )

    return DecisionCalibrationResponse(
        success=True,
        calibrationScore=score,
        delta=delta,
        insights=insights
    )


@router.post("/calibrate", response_model=DecisionCalibrationResponse)
def calibrate_decision_standard(data: DecisionCalibrationRequest):
    """Calibrate hypothetical decision confidence against reviewed evidence."""
    return _calculate_calibration(data)


@lab_router.post("/decision-lab/calibrate", response_model=DecisionCalibrationResponse)
def calibrate_decision_lab(data: DecisionCalibrationRequest):
    """Calibrate hypothetical decision confidence against reviewed evidence for Virtual Decision Lab."""
    return _calculate_calibration(data)


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
def record_initial_decision(
    decision_in: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Record an initial hypothetical decision in the Virtual Decision Lab."""
    service = DecisionService(db)
    user_id = current_user.id if current_user else None
    try:
        return service.record_initial_decision(decision_in, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{decision_id}/revise", response_model=DecisionResponse)
def record_decision_revision(
    decision_id: str,
    revision_in: DecisionRevise,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Record revised reasoning after reviewing evidence and interpretation forks."""
    service = DecisionService(db)
    existing = service.repository.get_by_id(decision_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Decision {decision_id} not found.")
    if existing.user_id is not None:
        if not current_user or current_user.id != existing.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: decision belongs to another user")
    try:
        return service.record_revision(decision_id, revision_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=List[DecisionResponse])
def list_user_decisions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve recorded decisions for the authenticated user."""
    service = DecisionService(db)
    user_id = current_user.id if current_user else None
    return service.list_decisions(user_id=user_id, skip=skip, limit=limit)


@lab_router.get("/decision-lab/scenarios")
@router.get("/scenarios")
def get_decision_lab_scenarios(db: Session = Depends(get_db)):
    """Retrieve available real practice scenarios for Virtual Decision Lab."""
    service = DecisionService(db)
    return service.get_scenarios()


@router.get("/{claim_id}", response_model=List[DecisionResponse])
def get_decisions_for_claim(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve decision records and sensitivity analysis for a claim."""
    service = DecisionService(db)
    return service.get_decisions_for_claim(claim_id)
