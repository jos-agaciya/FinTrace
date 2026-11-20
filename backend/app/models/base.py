import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseModelMixin:
    """Reusable mixin providing UUID primary keys and standard UTC timestamps."""
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
