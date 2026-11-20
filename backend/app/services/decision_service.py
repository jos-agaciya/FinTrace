import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.decision import DecisionModel
from backend.app.repositories.decision_repository import DecisionRepository
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.schemas.decision import DecisionCreate, DecisionRevise, DecisionSensitivitySummary, DecisionResponse


class DecisionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DecisionRepository(db)
        self.claim_repo = ClaimRepository(db)

    def record_initial_decision(self, decision_in: DecisionCreate) -> DecisionResponse:
        claim = self.claim_repo.get_by_id(decision_in.claim_id)
        if not claim:
            raise ValueError(f"Claim {decision_in.claim_id} not found.")

        assumptions_json = json.dumps(decision_in.assumptions_evaluated) if decision_in.assumptions_evaluated else None

        decision = DecisionModel(
            claim_id=decision_in.claim_id,
            interpretation_id=decision_in.interpretation_id,
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

            summary = DecisionSensitivitySummary(
                confidence_delta_points=conf_delta,
                allocation_delta_points=alloc_delta,
                reasoning_shift_type=shift_type,
                shift_explanation=expl
            )

        resp = DecisionResponse.model_validate(decision)
        resp.sensitivity_summary = summary
        return resp
