from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardProgressResponse,
    DashboardHistoryResponse
)
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Retrieve high-level overview metrics, recent claims, and recent decisions."""
    service = DashboardService(db)
    return service.get_overview()


@router.get("/progress", response_model=DashboardProgressResponse)
def get_dashboard_progress(session_id: str = Query(..., description="User or session identifier"), db: Session = Depends(get_db)):
    """Retrieve investor learning progress, baseline score, transfer score, and percentage-point delta."""
    service = DashboardService(db)
    return service.get_progress(session_id)


@router.get("/history", response_model=DashboardHistoryResponse)
def get_dashboard_history(session_id: str = Query(..., description="User or session identifier"), db: Session = Depends(get_db)):
    """Retrieve session-by-session assessment history."""
    service = DashboardService(db)
    return service.get_history(session_id)
