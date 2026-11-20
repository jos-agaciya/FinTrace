from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.claim import ClaimModel


class ClaimRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, claim: ClaimModel) -> ClaimModel:
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def get_by_id(self, claim_id: str) -> Optional[ClaimModel]:
        return self.db.query(ClaimModel).filter(ClaimModel.id == claim_id).first()

    def get_all(self, skip: int = 0, limit: int = 50) -> List[ClaimModel]:
        return self.db.query(ClaimModel).order_by(ClaimModel.submitted_at.desc()).offset(skip).limit(limit).all()

    def count(self) -> int:
        return self.db.query(ClaimModel).count()

    def delete(self, claim_id: str) -> bool:
        claim = self.get_by_id(claim_id)
        if not claim:
            return False
        self.db.delete(claim)
        self.db.commit()
        return True
