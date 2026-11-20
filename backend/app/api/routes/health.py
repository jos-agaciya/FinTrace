from fastapi import APIRouter, status
from pydantic import BaseModel
from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    version: str = "1.0.0"


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint to verify backend service status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV
    )
