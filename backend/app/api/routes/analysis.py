import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.analysis import AnalysisModel
from backend.app.models.claim import InterpretationForkModel
from backend.app.schemas.analysis import (
    AnalysisResponse,
    AnalysisDetailedResponse,
    InterpretationForkCreate,
    InterpretationForkResponse,
    CategorizedStatements
)
from backend.app.services.analysis_orchestrator import AnalysisOrchestrator

router = APIRouter(tags=["Analysis"])


def _format_analysis_detail(analysis: AnalysisModel, db: Session) -> AnalysisDetailedResponse:
    forks = db.query(InterpretationForkModel).filter_by(claim_id=analysis.claim_id).all()
    parsed_cats = json.loads(analysis.categorized_statements)
    missing = json.loads(analysis.missing_fields)

    return AnalysisDetailedResponse(
        analysis=AnalysisResponse.model_validate(analysis),
        categorized_statements_parsed=CategorizedStatements(**parsed_cats),
        missing_fields_list=missing,
        interpretation_forks=[InterpretationForkResponse.model_validate(f) for f in forks]
    )


@router.post("/analysis/{claim_id}/run", response_model=AnalysisDetailedResponse, status_code=status.HTTP_200_OK)
async def run_claim_analysis(claim_id: str, db: Session = Depends(get_db)):
    """
    Run multi-provider Decision Robustness Compiler workflow on a claim.
    Executes primary analysis, secondary review, deterministic validation,
    and epistemological categorization.
    """
    orchestrator = AnalysisOrchestrator(db)
    try:
        analysis = await orchestrator.run_analysis(claim_id)
        return _format_analysis_detail(analysis, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis pipeline error: {str(e)}")


@router.get("/analysis/{analysis_id}", response_model=AnalysisDetailedResponse)
def get_analysis_by_id(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed analysis result by analysis ID."""
    analysis = db.query(AnalysisModel).filter_by(id=analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis {analysis_id} not found")
    return _format_analysis_detail(analysis, db)


@router.get("/claims/{claim_id}/analysis", response_model=AnalysisDetailedResponse)
def get_latest_claim_analysis(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve the latest analysis result for a given claim."""
    analysis = db.query(AnalysisModel).filter_by(claim_id=claim_id).order_by(AnalysisModel.created_at.desc()).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No analysis found for claim {claim_id}")
    return _format_analysis_detail(analysis, db)


@router.get("/claims/{claim_id}/forks", response_model=List[InterpretationForkResponse])
def get_claim_interpretation_forks(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve generated interpretation forks for a claim."""
    forks = db.query(InterpretationForkModel).filter_by(claim_id=claim_id).all()
    return [InterpretationForkResponse.model_validate(f) for f in forks]


@router.post("/claims/{claim_id}/forks", response_model=InterpretationForkResponse, status_code=status.HTTP_201_CREATED)
def create_interpretation_fork(claim_id: str, fork_in: InterpretationForkCreate, db: Session = Depends(get_db)):
    """Manually add or customize an interpretation fork."""
    fork = InterpretationForkModel(
        claim_id=claim_id,
        title=fork_in.title,
        description=fork_in.description,
        ambiguous_phrase=fork_in.ambiguous_phrase,
        assumptions=json.dumps(fork_in.assumptions),
        information_required=fork_in.information_required,
        is_ai_generated=fork_in.is_ai_generated
    )
    db.add(fork)
    db.commit()
    db.refresh(fork)
    return InterpretationForkResponse.model_validate(fork)
