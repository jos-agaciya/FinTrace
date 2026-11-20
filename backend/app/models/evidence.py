from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class EvidenceModel(Base, BaseModelMixin):
    __tablename__ = "evidence"

    title = Column(String(512), nullable=False)
    document_title = Column(String(512), nullable=True)
    publisher = Column(String(255), nullable=False)
    source_url = Column(String(1024), nullable=False)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    retrieval_timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    evidence_category = Column(String(64), nullable=False)  # COMPANY_DISCLOSURE, MARKET_DATA, NEWS, REGULATORY, SYNTHETIC_BENCHMARK
    company_identifier = Column(String(64), nullable=True, index=True)
    company_symbol = Column(String(32), nullable=True, index=True)
    company_isin = Column(String(32), nullable=True, index=True)
    source_jurisdiction = Column(String(16), default="IN", nullable=False)  # IN, US, etc.
    exchange = Column(String(32), default="NSE", nullable=False)            # NSE, BSE, SEC, etc.
    content_summary = Column(Text, nullable=False)
    provenance_status = Column(String(32), default="REAL", nullable=False)  # REAL, SYNTHETIC, USER_PROVIDED, AI_GENERATED
    raw_payload = Column(Text, nullable=True)

    # Relationships
    claims = relationship("ClaimEvidenceModel", back_populates="evidence", cascade="all, delete-orphan")


class ClaimEvidenceModel(Base, BaseModelMixin):
    __tablename__ = "claim_evidence"

    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Float, default=1.0, nullable=False)
    association_notes = Column(Text, nullable=True)

    claim = relationship("ClaimModel", back_populates="evidence_associations")
    evidence = relationship("EvidenceModel", back_populates="claims")
