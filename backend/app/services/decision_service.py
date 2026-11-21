import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.decision import DecisionModel
from backend.app.models.claim import ClaimModel
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel
from backend.app.repositories.decision_repository import DecisionRepository
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.schemas.decision import DecisionCreate, DecisionRevise, DecisionSensitivitySummary, DecisionResponse


class DecisionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DecisionRepository(db)
        self.claim_repo = ClaimRepository(db)

    def record_initial_decision(self, decision_in: DecisionCreate, user_id: Optional[str] = None) -> DecisionResponse:
        claim = self.claim_repo.get_by_id(decision_in.claim_id)
        if not claim:
            raise ValueError(f"Claim {decision_in.claim_id} not found.")

        assumptions_json = json.dumps(decision_in.assumptions_evaluated) if decision_in.assumptions_evaluated else None

        decision = DecisionModel(
            claim_id=decision_in.claim_id,
            interpretation_id=decision_in.interpretation_id,
            user_id=user_id,
            initial_thesis=decision_in.initial_thesis,
            initial_confidence=decision_in.initial_confidence,
            initial_allocation=decision_in.initial_allocation,
            assumptions_evaluated=assumptions_json
        )
        created = self.repository.create(decision)
        return self._build_response(created)

    def record_revision(self, decision_id: str, revision_in: DecisionRevise) -> DecisionResponse:
        decision = self.repository.get_by_id(decision_id)
        if not decision:
            raise ValueError(f"Decision record {decision_id} not found.")

        decision.revised_thesis = revision_in.revised_thesis
        decision.revised_confidence = revision_in.revised_confidence
        decision.revised_allocation = revision_in.revised_allocation
        decision.reason_for_change = revision_in.reason_for_change

        if revision_in.assumptions_evaluated is not None:
            decision.assumptions_evaluated = json.dumps(revision_in.assumptions_evaluated)

        updated = self.repository.update(decision)
        return self._build_response(updated)

    def get_decisions_for_claim(self, claim_id: str) -> List[DecisionResponse]:
        records = self.repository.get_by_claim_id(claim_id)
        return [self._build_response(r) for r in records]

    def list_decisions(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[DecisionResponse]:
        query = self.db.query(DecisionModel)
        if user_id:
            query = query.filter(DecisionModel.user_id == user_id)
        records = query.order_by(DecisionModel.created_at.desc()).offset(skip).limit(limit).all()
        return [self._build_response(r) for r in records]

    def get_scenarios(self) -> List[dict]:
        """Retrieve available practice scenarios based on persisted claims, evidence and forks."""
        claims = self.db.query(ClaimModel).order_by(ClaimModel.submitted_at.desc()).limit(10).all()
        if not claims:
            try:
                from backend.app.integrations.ai_engine_adapter import AIEngineAdapter
                adapter = AIEngineAdapter.get_instance()
                practice = adapter.generate_practice_claim(template_category="VAGUE_TIMEFRAME")
            except Exception:
                practice = None

            practice_text = (
                practice["claim_text"]
                if practice and practice.get("claim_text")
                else "Apex Dynamics Ltd. will expand operating margin by 25% in the near term driven by automation."
            )
            company_name = (
                practice["target_entity"]
                if practice and practice.get("target_entity")
                else "Apex Dynamics Ltd."
            )

            cf_claim = ClaimModel(
                original_claim=practice_text,
                company_name=company_name,
                ticker="APEX",
                claim_direction="BULLISH",
                provenance_status="SYNTHETIC",
                is_ambiguous_entity=False
            )
            self.db.add(cf_claim)
            self.db.commit()
            self.db.refresh(cf_claim)

            ev1 = EvidenceModel(
                title=f"{company_name} Q3 Operating Filing",
                publisher="SEC EDGAR Disclosures",
                source_url="https://fintrace.ai/disclosures/apex-q3",
                publication_date=datetime.now(timezone.utc),
                evidence_category="FINANCIAL_FILING",
                company_symbol="APEX",
                source_jurisdiction="US",
                exchange="SEC",
                content_summary="Historical operating margin was 14.2%. Supply chain constraints and chip shortages extend automation lead times by 9 to 12 months.",
                provenance_status="SYNTHETIC"
            )
            ev2 = EvidenceModel(
                title=f"{company_name} Order Backlog Disclosure",
                publisher="SEC EDGAR Disclosures",
                source_url="https://fintrace.ai/disclosures/apex-orders",
                publication_date=datetime.now(timezone.utc),
                evidence_category="CONTRACT_DISCLOSURE",
                company_symbol="APEX",
                source_jurisdiction="US",
                exchange="SEC",
                content_summary="Contracted order backlog reached $480M across enterprise customers, scheduled for phased delivery over 24 months.",
                provenance_status="SYNTHETIC"
            )
            self.db.add_all([ev1, ev2])
            self.db.commit()
            self.db.refresh(ev1)
            self.db.refresh(ev2)

            assoc1 = ClaimEvidenceModel(claim_id=cf_claim.id, evidence_id=ev1.id, relevance_score=0.9, association_notes="Contradictory margin timing risk")
            assoc2 = ClaimEvidenceModel(claim_id=cf_claim.id, evidence_id=ev2.id, relevance_score=0.85, association_notes="Supporting customer demand backlog")
            self.db.add_all([assoc1, assoc2])
            self.db.commit()
            self.db.refresh(cf_claim)
            claims = [cf_claim]

        scenarios = []
        for c in claims:
            ev_items = []
            for assoc in (c.evidence_associations or []):
                ev = assoc.evidence
                ev_type = "negative" if ("contradict" in (assoc.association_notes or "").lower() or "risk" in (ev.title or "").lower()) else "positive"
                ev_items.append({
                    "id": ev.id,
                    "type": ev_type,
                    "category": ev.evidence_category or "Statutory Disclosure",
                    "title": ev.title,
                    "detail": ev.content_summary,
                    "source": f"{ev.publisher} · {ev.exchange}",
                    "url": ev.source_url
                })

            learning_outcomes = {
                "changedMind": "By inspecting statutory disclosures and alternative interpretation forks, you avoided relying on unhedged short-term assumptions.",
                "keptMindCautious": "You maintained a disciplined, evidence-calibrated perspective despite directional market sentiment.",
                "keptMindOverconfident": "You maintained high assertiveness despite identified invalidation conditions and unstated assumptions."
            }

            scenarios.append({
                "id": c.id,
                "ticker": (c.ticker or "CORP").upper(),
                "company": c.company_name or "Analyzed Corporate Entity",
                "sector": "Corporate Equity & Statutory Disclosures",
                "badge": "PERSISTED DISCLOSURE SCENARIO",
                "title": f"{c.company_name or c.ticker}: {c.original_claim[:70]}",
                "summary": c.original_claim,
                "firstImpressionQuestion": f"Given the statement regarding {c.company_name or c.ticker}, what is your initial directional stance?",
                "defaultInitialRationale": f"Initial thesis regarding {c.company_name or c.ticker}'s operational forecast.",
                "evidenceItems": ev_items,
                "learningOutcomes": learning_outcomes
            })
        return scenarios

    def _build_response(self, decision: DecisionModel) -> DecisionResponse:
        summary: Optional[DecisionSensitivitySummary] = None

        if decision.revised_confidence is not None and decision.revised_allocation is not None:
            conf_delta = decision.revised_confidence - decision.initial_confidence
            alloc_delta = decision.revised_allocation - decision.initial_allocation

            if alloc_delta < 0:
                shift_type = "REDUCED_EXPOSURE"
                expl = f"Allocation decreased by {abs(alloc_delta):.1f} percentage points following counter-evidence review."
            elif alloc_delta > 0:
                shift_type = "INCREASED_EXPOSURE"
                expl = f"Allocation increased by {alloc_delta:.1f} percentage points following confirmation of thesis."
            elif abs(conf_delta) > 5.0:
                shift_type = "CONVICTION_SHIFT"
                expl = f"Allocation remained steady while confidence shifted by {conf_delta:+.1f} percentage points."
            else:
                shift_type = "UNCHANGED"
                expl = "Reasoning and exposure remained calibrated despite alternative interpretations."

            # Enrich explanation via AI Engine DecisionSensitivityEngine if available
            try:
                from backend.app.integrations.ai_engine_adapter import AIEngineAdapter
                adapter = AIEngineAdapter.get_instance()
                if adapter.is_available:
                    ai_expl = adapter.explain_decision_sensitivity(
                        initial_confidence=decision.initial_confidence,
                        initial_allocation=decision.initial_allocation,
                        initial_thesis=decision.initial_thesis,
                        revised_confidence=decision.revised_confidence,
                        revised_allocation=decision.revised_allocation,
                        revised_thesis=decision.revised_thesis or "",
                    )
                    if ai_expl and ai_expl.get("summary_of_change"):
                        expl = f"{expl} {ai_expl['summary_of_change']}"
            except Exception:
                pass

            summary = DecisionSensitivitySummary(
                confidence_delta_points=conf_delta,
                allocation_delta_points=alloc_delta,
                reasoning_shift_type=shift_type,
                shift_explanation=expl
            )

        resp = DecisionResponse.model_validate(decision)
        resp.sensitivity_summary = summary
        return resp
