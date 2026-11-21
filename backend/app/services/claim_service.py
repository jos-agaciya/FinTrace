from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.claim import ClaimModel
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.schemas.claim import ClaimCreate
from backend.app.validators.claim_validator import ClaimValidator


class ClaimService:
    def __init__(self, db: Session):
        self.repository = ClaimRepository(db)
        self.validator = ClaimValidator()

    def submit_claim(self, claim_in: ClaimCreate, user_id: Optional[str] = None) -> ClaimModel:
        """
        Ingests a financial claim, preserves original text untouched,
        extracts explicit facts, and strictly preserves missing details as None.
        """
        extracted = self.validator.extract_structured_fields(
            claim_text=claim_in.original_claim,
            existing_fields=claim_in.model_dump(exclude_unset=True)
        )

        claim_model = ClaimModel(
            original_claim=claim_in.original_claim,
            source_url=claim_in.source_url,
            source_platform=claim_in.source_platform,
            provenance_status=claim_in.provenance_status.value,
            user_id=user_id,
            company_name=extracted.get("company_name"),
            ticker=extracted.get("ticker"),
            exchange=extracted.get("exchange"),
            claim_direction=extracted.get("claim_direction"),
            target_value=extracted.get("target_value"),
            target_unit=extracted.get("target_unit"),
            time_horizon=extracted.get("time_horizon"),
            entry_condition=extracted.get("entry_condition"),
            exit_condition=extracted.get("exit_condition"),
            invalidation_condition=extracted.get("invalidation_condition"),
            evidence_or_rationale=extracted.get("evidence_or_rationale"),
            is_ambiguous_entity=extracted.get("is_ambiguous_entity", False),
            entity_ambiguity_notes=extracted.get("entity_ambiguity_notes")
        )

        return self.repository.create(claim_model)

    def get_claim(self, claim_id: str) -> Optional[ClaimModel]:
        return self.repository.get_by_id(claim_id)

    def list_claims(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> Tuple[List[ClaimModel], int]:
        total = self.repository.count(user_id=user_id)
        items = self.repository.get_all(user_id=user_id, skip=skip, limit=limit)
        return items, total

    def delete_claim(self, claim_id: str) -> bool:
        return self.repository.delete(claim_id)
