from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel


class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_evidence(self, evidence: EvidenceModel) -> EvidenceModel:
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceModel]:
        return self.db.query(EvidenceModel).filter(EvidenceModel.id == evidence_id).first()

    def associate_with_claim(
        self,
        claim_id: str,
        evidence_id: str,
        relevance_score: float = 1.0,
        notes: Optional[str] = None
    ) -> ClaimEvidenceModel:
        assoc = ClaimEvidenceModel(
            claim_id=claim_id,
            evidence_id=evidence_id,
            relevance_score=relevance_score,
            association_notes=notes
        )
        self.db.add(assoc)
        self.db.commit()
        self.db.refresh(assoc)
        return assoc

    def get_claim_evidence(self, claim_id: str) -> List[ClaimEvidenceModel]:
        return self.db.query(ClaimEvidenceModel).filter(ClaimEvidenceModel.claim_id == claim_id).all()
