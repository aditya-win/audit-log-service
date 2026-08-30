from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.audit_event import AuditEvent
from typing import List, Optional

class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_latest_event(self) -> Optional[AuditEvent]:
        return self.session.execute(
            select(AuditEvent).order_by(desc(AuditEvent.id)).limit(1)
        ).scalar_one_or_none()

    def create(self, event: AuditEvent) -> AuditEvent:
        # Append only
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_all_ordered_iterator(self):
        # Using yield_per for memory efficient iteration
        return self.session.execute(
            select(AuditEvent).order_by(AuditEvent.id)
        ).scalars()
