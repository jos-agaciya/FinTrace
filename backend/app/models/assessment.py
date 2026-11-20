from sqlalchemy import Column, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin


class AssessmentModel(Base, BaseModelMixin):
    """Tracks investor evaluation ability across Baseline, Assisted Practice, and Independent Transfer."""
    __tablename__ = "assessments"

    session_id = Column(String(64), nullable=False, index=True)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_stage = Column(String(32), nullable=False)  # BASELINE, ASSISTED_PRACTICE, INDEPENDENT_TRANSFER

    # Five-dimension deterministic rubric scores (each 0 - 20, composite 0 - 100)
    score_evidence_eval = Column(Float, nullable=False)
    score_claim_specificity = Column(Float, nullable=False)
    score_risk_awareness = Column(Float, nullable=False)
    score_assumption_awareness = Column(Float, nullable=False)
    score_confidence_calibration = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)

    # User submission and detailed rubric feedback
    user_responses = Column(Text, nullable=False)          # JSON-encoded answers
    rubric_feedback = Column(Text, nullable=False)         # JSON-encoded feedback per dimension

    # Relationship
    claim = relationship("ClaimModel", back_populates="assessments")
