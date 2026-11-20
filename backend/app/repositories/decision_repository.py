from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.decision import DecisionModel


class DecisionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, decision: DecisionModel) -> DecisionModel:
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def get_by_id(self, decision_id: str) -> Optional[DecisionModel]:
        return self.db.query(DecisionModel).filter(DecisionModel.id == decision_id).first()

    def get_by_claim_id(self, claim_id: str) -> List[DecisionModel]:
        return self.db.query(DecisionModel).filter(DecisionModel.claim_id == claim_id).order_by(DecisionModel.created_at.desc()).all()

    def update(self, decision: DecisionModel) -> DecisionModel:
        self.db.commit()
        self.db.refresh(decision)
        return decision
