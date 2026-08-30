from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.models.base import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String, index=True, nullable=False)
    actor_id = Column(String, index=True, nullable=False)
    resource_type = Column(String, index=True, nullable=False)
    resource_id = Column(String, index=True, nullable=False)
    payload = Column(String, nullable=True) # Nullable for archival
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False, default=lambda: datetime.now(timezone.utc))
    previous_hash = Column(String, nullable=False)
    current_hash = Column(String, nullable=False)
    is_archived = Column(Integer, default=0, nullable=False) # 0 or 1 for sqlite boolean
    redacted_fields = Column(String, nullable=True) # JSON string mapping field -> hash
