from sqlalchemy import Column, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class ClaimModel(Base, BaseModelMixin):
    __tablename__ = "claims"

    # Core claim text & source
    original_claim = Column(Text, nullable=False)
    source_url = Column(String(512), nullable=True)
    source_platform = Column(String(64), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Structured extraction fields (strictly nullable if not stated)
    company_name = Column(String(255), nullable=True)
    ticker = Column(String(32), nullable=True)
    exchange = Column(String(32), nullable=True)
    claim_direction = Column(String(32), nullable=True)  # BULLISH, BEARISH, NEUTRAL, UNKNOWN
    target_value = Column(Float, nullable=True)
    target_unit = Column(String(32), nullable=True)     # %, INR, USD, etc.
    time_horizon = Column(String(128), nullable=True)
    entry_condition = Column(Text, nullable=True)
    exit_condition = Column(Text, nullable=True)
    invalidation_condition = Column(Text, nullable=True)
    evidence_or_rationale = Column(Text, nullable=True)

    # Provenance and Ambiguity status
    provenance_status = Column(String(32), default="USER_PROVIDED", nullable=False)  # REAL, SYNTHETIC, USER_PROVIDED, AI_GENERATED
    is_ambiguous_entity = Column(Boolean, default=False, nullable=False)
    entity_ambiguity_notes = Column(Text, nullable=True)

    # Relationships
    interpretation_forks = relationship("InterpretationForkModel", back_populates="claim", cascade="all, delete-orphan")
    analyses = relationship("AnalysisModel", back_populates="claim", cascade="all, delete-orphan")
    evidence_associations = relationship("ClaimEvidenceModel", back_populates="claim", cascade="all, delete-orphan")
    decisions = relationship("DecisionModel", back_populates="claim", cascade="all, delete-orphan")
    assessments = relationship("AssessmentModel", back_populates="claim", cascade="all, delete-orphan")


class InterpretationForkModel(Base, BaseModelMixin):
    __tablename__ = "interpretation_forks"

    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    ambiguous_phrase = Column(String(255), nullable=False)
    assumptions = Column(Text, nullable=False)  # JSON-encoded array of assumptions
    information_required = Column(Text, nullable=False)
    is_ai_generated = Column(Boolean, default=True, nullable=False)

    # Relationship
    claim = relationship("ClaimModel", back_populates="interpretation_forks")
    decisions = relationship("DecisionModel", back_populates="interpretation_fork")
