from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.assessment import AssessmentModel


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, assessment: AssessmentModel) -> AssessmentModel:
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_by_id(self, assessment_id: str) -> Optional[AssessmentModel]:
        return self.db.query(AssessmentModel).filter(AssessmentModel.id == assessment_id).first()

    def get_by_session(self, session_id: str) -> List[AssessmentModel]:
        return self.db.query(AssessmentModel).filter(AssessmentModel.session_id == session_id).order_by(AssessmentModel.created_at.asc()).all()

    def get_latest_by_stage(self, session_id: str, stage: str) -> Optional[AssessmentModel]:
        return (
            self.db.query(AssessmentModel)
            .filter(AssessmentModel.session_id == session_id, AssessmentModel.assessment_stage == stage)
            .order_by(AssessmentModel.created_at.desc())
            .first()
        )
