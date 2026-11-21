from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import UserModel
from backend.app.api.deps import get_current_user_optional
from backend.app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardProgressResponse,
    DashboardHistoryResponse
)
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve high-level overview metrics, recent claims, and recent decisions for authenticated user."""
    service = DashboardService(db)
    user_id = current_user.id if current_user else None
    return service.get_overview(user_id=user_id)


@router.get("/progress", response_model=DashboardProgressResponse)
def get_dashboard_progress(
    session_id: Optional[str] = Query(None, description="User or session identifier"),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve investor learning progress, baseline score, transfer score, and percentage-point delta."""
    service = DashboardService(db)
    target_session = session_id or (current_user.id if current_user else "default_session")
    return service.get_progress(target_session)


@router.get("/history", response_model=DashboardHistoryResponse)
def get_dashboard_history(
    session_id: Optional[str] = Query(None, description="User or session identifier"),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve session-by-session assessment history."""
    service = DashboardService(db)
    target_session = session_id or (current_user.id if current_user else "default_session")
    return service.get_history(target_session)
