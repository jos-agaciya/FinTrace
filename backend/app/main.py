from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.claims import router as claims_router
from backend.app.api.routes.evidence import router as evidence_router
from backend.app.api.routes.analysis import router as analysis_router
from backend.app.api.routes.decisions import router as decisions_router, lab_router as decision_lab_router
from backend.app.api.routes.assessments import router as assessments_router
from backend.app.api.routes.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="FinTrace Backend API: AI-Powered Investor Decision Intelligence & Robustness Compiler",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under primary prefix (/api/v1)
api_routers = [
    health_router,
    auth_router,
    claims_router,
    evidence_router,
    analysis_router,
    decisions_router,
    decision_lab_router,
    assessments_router,
    dashboard_router,
]

for r in api_routers:
    app.include_router(r, prefix=settings.API_V1_PREFIX)

# Also register under /api prefix for seamless frontend compatibility
for r in api_routers:
    app.include_router(r, prefix="/api")

# Also register decision_lab_router at root so /decision-lab/calibrate works directly
app.include_router(decision_lab_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
