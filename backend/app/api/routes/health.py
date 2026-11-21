from typing import Optional, Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel
from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    version: str = "1.0.0"
    ai_engine: Optional[Dict[str, Any]] = None


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint to verify backend service and AI engine status."""
    ai_status = {"status": "unloaded"}
    try:
        from backend.app.integrations.ai_engine_adapter import AIEngineAdapter
        adapter = AIEngineAdapter.get_instance()
        ai_status = adapter.get_health_status()
    except Exception as e:
        ai_status = {"status": "degraded", "error": str(e)}

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        ai_engine=ai_status
    )
