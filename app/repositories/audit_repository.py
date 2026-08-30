from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventQuery
from typing import List, Optional

class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_latest_event(self) -> Optional[AuditEvent]:
        return self.session.execute(
            select(AuditEvent).order_by(desc(AuditEvent.id)).limit(1)
        ).scalar_one_or_none()

    def create(self, event: AuditEvent) -> AuditEvent:
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_all_ordered_iterator(self):
        return self.session.execute(
            select(AuditEvent).order_by(AuditEvent.id)
        ).scalars()

    def get_by_id(self, event_id: int) -> Optional[AuditEvent]:
        return self.session.query(AuditEvent).filter(AuditEvent.id == event_id).first()

    def get_filtered(self, query: AuditEventQuery) -> List[AuditEvent]:
        stmt = select(AuditEvent)
        
        if query.actorId:
            stmt = stmt.filter(AuditEvent.actor_id == query.actorId)
        if query.resourceType:
            stmt = stmt.filter(AuditEvent.resource_type == query.resourceType)
        if query.resourceId:
            stmt = stmt.filter(AuditEvent.resource_id == query.resourceId)
        if query.eventType:
            stmt = stmt.filter(AuditEvent.event_type == query.eventType.value)
        if query.from_date:
            stmt = stmt.filter(AuditEvent.timestamp >= query.from_date)
        if query.to_date:
            stmt = stmt.filter(AuditEvent.timestamp <= query.to_date)
            
        offset = (query.page - 1) * query.pageSize
        stmt = stmt.order_by(desc(AuditEvent.timestamp)).offset(offset).limit(query.pageSize)
        
        return list(self.session.execute(stmt).scalars().all())
