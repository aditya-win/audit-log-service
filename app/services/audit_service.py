from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.utils.hashing import calculate_hash, GENESIS_HASH
from app.utils.canonical_json import to_canonical_json
from app.schemas.audit import AuditEventCreate, AuditEventQuery

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def append_event(self, event_in: AuditEventCreate) -> AuditEvent:
        latest = self.repository.get_latest_event()
        previous_hash = latest.current_hash if latest else GENESIS_HASH
        
        timestamp = event_in.timestamp or datetime.now(timezone.utc)
        payload_str = to_canonical_json(event_in.payload)
        
        current_hash = calculate_hash(
            event_type=event_in.eventType.value,
            actor_id=event_in.actorId,
            resource_type=event_in.resourceType,
            resource_id=event_in.resourceId,
            payload_str=payload_str,
            timestamp=timestamp,
            previous_hash=previous_hash
        )
        
        event = AuditEvent(
            event_type=event_in.eventType.value,
            actor_id=event_in.actorId,
            resource_type=event_in.resourceType,
            resource_id=event_in.resourceId,
            payload=payload_str,
            timestamp=timestamp,
            previous_hash=previous_hash,
            current_hash=current_hash
        )
        return self.repository.create(event)

    def get_event(self, event_id: int) -> Optional[AuditEvent]:
        return self.repository.get_by_id(event_id)

    def get_events(self, query: AuditEventQuery) -> list[AuditEvent]:
        return self.repository.get_filtered(query)
