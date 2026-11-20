from sqlalchemy import Column, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class AnalysisModel(Base, BaseModelMixin):
    __tablename__ = "analyses"

    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)

    # Provider metadata
    primary_provider = Column(String(32), nullable=False)    # groq, gemini
    secondary_provider = Column(String(32), nullable=False)  # gemini, groq
    provider_status = Column(String(32), nullable=False)     # SUCCESS, FALLBACK_USED, NEEDS_VERIFICATION, PROVIDER_UNAVAILABLE, VALIDATION_FAILED
    fallback_reason = Column(Text, nullable=True)

    # Falsifiability evaluation
    falsifiability_score = Column(Float, nullable=False)  # 0 to 100
    missing_fields = Column(Text, nullable=False)         # JSON list of missing fields
    testability_explanation = Column(Text, nullable=False)

    # Categorized statements for epistemological clarity
    # JSON-encoded object: {"SOURCE_FACT": [], "AI_INTERPRETATION": [], "USER_ASSUMPTION": [], "UNRESOLVED_QUESTION": []}
    categorized_statements = Column(Text, nullable=False)

    # Deterministic validation output
    validation_status = Column(String(32), nullable=False)  # PASSED, FAILED, WARNING
    validation_notes = Column(Text, nullable=True)          # JSON list of deterministic validation issues

    # Raw model summaries / audit trail
    primary_output_summary = Column(Text, nullable=True)
    secondary_output_summary = Column(Text, nullable=True)

    # Relationship
    claim = relationship("ClaimModel", back_populates="analyses")
