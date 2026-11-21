from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class UserModel(Base, BaseModelMixin):
    """User account entity for authentication, authorization, and multi-tenant isolation."""
    __tablename__ = "users"

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(100), default="Retail Investor & Decision Analyst", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships to user-owned domain resources
    claims = relationship("ClaimModel", back_populates="user")
    decisions = relationship("DecisionModel", back_populates="user")
