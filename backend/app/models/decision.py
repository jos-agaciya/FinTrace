from sqlalchemy import Column, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class DecisionModel(Base, BaseModelMixin):
    """Tracks hypothetical decisions in the Virtual Decision Lab without real-money trading."""
    __tablename__ = "decisions"

    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    interpretation_id = Column(String(36), ForeignKey("interpretation_forks.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Initial stance
    initial_thesis = Column(Text, nullable=False)
    initial_confidence = Column(Float, nullable=False)      # 0 to 100
    initial_allocation = Column(Float, nullable=False)      # Virtual percentage or amount

    # Revised stance after reviewing evidence & forks
    revised_thesis = Column(Text, nullable=True)
    revised_confidence = Column(Float, nullable=True)
    revised_allocation = Column(Float, nullable=True)

    reason_for_change = Column(Text, nullable=True)
    assumptions_evaluated = Column(Text, nullable=True)     # JSON list of user assumptions
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="decisions")
    claim = relationship("ClaimModel", back_populates="decisions")
    interpretation_fork = relationship("InterpretationForkModel", back_populates="decisions")
