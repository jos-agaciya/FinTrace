import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.claim import ClaimModel, InterpretationForkModel
from backend.app.models.analysis import AnalysisModel
from backend.app.models.user import UserModel
from backend.app.api.deps import get_current_user_optional
from backend.app.schemas.claim import (
    ClaimCreate,
    ClaimResponse,
    ClaimListResponse,
    ClaimAnalyzeRequest
)
from backend.app.services.claim_service import ClaimService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.analysis_orchestrator import AnalysisOrchestrator

router = APIRouter(prefix="/claims", tags=["Claims"])


def _enrich_claim_response(claim: ClaimModel, db: Session) -> ClaimResponse:
    resp = ClaimResponse.model_validate(claim)
    resp.company = claim.company_name or "Analyzed Entity"
    resp.statement = claim.original_claim
    resp.date = claim.created_at.strftime("%d %b %Y")
    
    dir_val = (claim.claim_direction or "Bullish").upper()
    if "BULL" in dir_val:
        resp.direction = "Bullish"
    elif "BEAR" in dir_val:
        resp.direction = "Bearish"
    else:
        resp.direction = "Neutral"

    resp.horizon = claim.time_horizon or "Unspecified horizon"
    resp.targetPrice = f"${claim.target_value:,.2f}" if claim.target_value else None

    # Get forks
    forks = db.query(InterpretationForkModel).filter_by(claim_id=claim.id).all()
    # Get latest analysis
    analysis = db.query(AnalysisModel).filter_by(claim_id=claim.id).order_by(AnalysisModel.created_at.desc()).first()
    # Get evidence
    evidence_assocs = EvidenceService(db).get_claim_evidence(claim.id)

    missing_fields_list = []
    if analysis and analysis.missing_fields:
        try:
            loaded = json.loads(analysis.missing_fields)
            if isinstance(loaded, list):
                missing_fields_list = [str(x) for x in loaded if str(x).strip()]
        except Exception:
            missing_fields_list = []
    if not missing_fields_list:
        # Dynamically determine missing falsifiability parameters from claim structure
        if not claim.target_value:
            missing_fields_list.append("Quantitative target metric or price boundary not specified")
        if not claim.time_horizon:
            missing_fields_list.append("Definite time horizon for claim realization not specified")
        if not claim.invalidation_condition:
            missing_fields_list.append("Explicit invalidation condition or falsification threshold not stated")
        if not claim.entry_condition:
            missing_fields_list.append("Prerequisite entry or market conditions not stated")

    falsifiability = analysis.falsifiability_score if analysis else 0.0
    if not evidence_assocs:
        validation_status = "Insufficient Evidence"
        coverage = 0
    elif analysis and analysis.validation_status == "DEGRADED":
        validation_status = "Degraded (No AI Provider)"
        coverage = min(max(int(round(len(evidence_assocs) * 20)), 20), 80)
    elif analysis and analysis.validation_status == "PASSED":
        validation_status = "Completed"
        coverage = min(max(int(round(falsifiability * 0.7 + len(evidence_assocs) * 10)), 35), 95)
    else:
        validation_status = "Needs Verification"
        coverage = min(max(int(round(falsifiability * 0.5 + len(evidence_assocs) * 10)), 25), 85)

    resp.validationStatus = validation_status
    resp.evidenceCoverage = coverage
    resp.breakdown = {
        "statedTarget": f"{claim.target_value} {claim.target_unit or ''}".strip() if claim.target_value else "Target not specified",
        "impliedHorizon": claim.time_horizon or "Unspecified timeframe",
        "primaryCatalyst": analysis.testability_explanation if analysis else "Extracted catalyst mechanism",
        "missingConditions": missing_fields_list
    }
    resp.completeness = {
        "score": int(round(falsifiability)),
        "provenanceStatus": claim.provenance_status,
        "identifiedAssumptions": max(len(missing_fields_list), 1),
        "testedAssumptions": len(evidence_assocs)
    }

    interpretations = []
    for f in forks:
        title_lower = f.title.lower()
        stance = "Bullish"
        if "bear" in title_lower or "drag" in title_lower or "speculative" in title_lower or "risk" in title_lower or "headwind" in title_lower:
            stance = "Bearish Risk"
        elif "neutral" in title_lower or "cautious" in title_lower or "simulation" in title_lower:
            stance = "Neutral / Cautious"

        interpretations.append({
            "fork": f.title,
            "stance": stance,
            "rationale": f.description,
            "source": "AI-GENERATED FORK" if f.is_ai_generated else "ANALYST_DEFINED"
        })
    if not interpretations:
        dir_label = (claim.claim_direction or "Bullish").capitalize()
        entity_label = claim.company_name or claim.ticker or "Target Issuer"
        interpretations = [
            {
                "fork": f"Primary Thesis ({dir_label})",
                "stance": "Bullish" if "bull" in dir_label.lower() else ("Bearish Risk" if "bear" in dir_label.lower() else "Neutral / Cautious"),
                "rationale": f"Interprets statement as a direct operational forecast for {entity_label}.",
                "source": "AI-GENERATED FORK"
            }
        ]
    resp.interpretations = interpretations

    supporting = []
    contradictory = []
    # Semantic sentiment and directional indicators
    risk_keywords = [
        "loss", "investigation", "penalty", "resignation", "decline", "warning",
        "violation", "adverse", "litigation", "drag", "headwind", "delay",
        "chokepoint", "bottleneck", "deficit", "drop", "weakness", "fall",
        "impairment", "downturn", "default", "restructuring", "slowdown"
    ]
    growth_keywords = [
        "growth", "expansion", "surge", "backlog", "patent", "increase",
        "profit", "revenue", "gain", "order", "award", "outperform",
        "positive", "beat", "dividend", "record", "acceleration"
    ]
    is_bullish = "bull" in dir_val.lower()
    is_bearish = "bear" in dir_val.lower()

    for a in evidence_assocs:
        ev = a.evidence
        ev_item = {
            "id": ev.id,
            "title": ev.title,
            "source": f"{ev.publisher} · {ev.exchange}",
            "date": ev.publication_date.strftime("%d %b %Y") if ev.publication_date else "Recent Disclosure",
            "provenance": ev.provenance_status,
            "excerpt": ev.content_summary,
            "url": ev.source_url
        }
        is_contra = False
        if a.association_notes and "contradict" in a.association_notes.lower():
            is_contra = True
        elif a.association_notes and "support" in a.association_notes.lower():
            is_contra = False
        else:
            corpus = f"{ev.title} {ev.content_summary} {ev.raw_payload or ''}".lower()
            risk_matches = sum(corpus.count(k) for k in risk_keywords)
            growth_matches = sum(corpus.count(k) for k in growth_keywords)

            if is_bullish:
                if risk_matches > growth_matches:
                    is_contra = True
            elif is_bearish:
                if growth_matches > risk_matches:
                    is_contra = True

        if is_contra:
            contradictory.append(ev_item)
        else:
            supporting.append(ev_item)

    resp.supportingEvidence = supporting
    resp.contradictoryEvidence = contradictory
    return resp


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
def submit_claim(
    claim_in: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Submit a new financial claim for analysis."""
    service = ClaimService(db)
    user_id = current_user.id if current_user else None
    return service.submit_claim(claim_in, user_id=user_id)


@router.post("/analyze", response_model=ClaimResponse, status_code=status.HTTP_200_OK)
async def analyze_claim_convenience(
    req: ClaimAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Convenience workflow: Submits claim, retrieves external evidence, runs robustness analysis, and returns consolidated report."""
    raw_statement = (req.statement or req.original_claim or "").strip()
    if not raw_statement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statement text is required for analysis."
        )

    ticker = req.ticker
    company = req.company or req.company_name
    source_url = req.sourceUrl or req.source_url
    horizon = req.horizon or req.time_horizon

    # 1. Ingest claim
    claim_service = ClaimService(db)
    claim_in = ClaimCreate(
        original_claim=raw_statement,
        source_url=source_url,
        company_name=company,
        ticker=ticker,
        time_horizon=horizon
    )
    user_id = current_user.id if current_user else None
    claim = claim_service.submit_claim(claim_in, user_id=user_id)

    # 2. Trigger evidence retrieval
    evidence_service = EvidenceService(db)
    await evidence_service.retrieve_for_claim(claim.id)

    # 3. Run Analysis Orchestrator
    orchestrator = AnalysisOrchestrator(db)
    await orchestrator.run_analysis(claim.id)

    # 4. Return enriched consolidated claim
    return _enrich_claim_response(claim, db)


@router.get("", response_model=ClaimListResponse)
def list_claims(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve history of submitted claims."""
    service = ClaimService(db)
    user_id = current_user.id if current_user else None
    items, total = service.list_claims(user_id=user_id, skip=skip, limit=limit)
    enriched_items = [_enrich_claim_response(c, db) for c in items]
    return ClaimListResponse(total=total, items=enriched_items)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve an individual claim by ID with user ownership check."""
    service = ClaimService(db)
    claim = service.get_claim(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with ID {claim_id} not found"
        )
    if claim.user_id is not None:
        if not current_user or current_user.id != claim.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: claim belongs to another user"
            )
    return _enrich_claim_response(claim, db)


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Delete a user-submitted claim with user ownership check."""
    service = ClaimService(db)
    claim = service.get_claim(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with ID {claim_id} not found"
        )
    if claim.user_id is not None:
        if not current_user or current_user.id != claim.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: claim belongs to another user"
            )
    service.delete_claim(claim_id)
    return None
