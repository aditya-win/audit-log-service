import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.utils.hashing import calculate_hash, GENESIS_HASH
from app.utils.canonical_json import to_canonical_json
from app.schemas.audit import AuditEventCreate, AuditEventQuery

_append_lock = threading.Lock()

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def append_event(self, event_in: AuditEventCreate) -> AuditEvent:
        with _append_lock:
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

    def archive_record(self, event_id: int) -> bool:
        event = self.repository.get_by_id(event_id)
        if not event or event.is_archived:
            return False
            
        event.payload = None
        event.is_archived = 1
        self.repository.session.commit()
        return True

    def redact_record(self, event_id: int, field_keys: list[str]) -> bool:
        import json
        import hashlib
        import hmac
        from app.config import settings
        
        event = self.repository.get_by_id(event_id)
        if not event or event.is_archived:
            return False
            
        payload = json.loads(event.payload)
        redacted = json.loads(event.redacted_fields) if event.redacted_fields else {}
        modified = False
        salt_bytes = settings.redaction_salt.encode('utf-8')
        
        for key in field_keys:
            if key in payload:
                val_str = str(payload[key])
                redacted[key] = hmac.new(salt_bytes, val_str.encode('utf-8'), hashlib.sha256).hexdigest()
                payload[key] = "<REDACTED>"
                modified = True
                
        if modified:
            event.payload = json.dumps(payload, separators=(',', ':'), sort_keys=True)
            event.redacted_fields = json.dumps(redacted, separators=(',', ':'), sort_keys=True)
            self.repository.session.commit()
            return True
            
        return False
        
    def export_records(self, actor_id: str = None, resource_id: str = None) -> dict:
        query = AuditEventQuery(actorId=actor_id, resourceId=resource_id, pageSize=100)
        events = self.repository.get_filtered(query)
        
        records = []
        for e in events:
            records.append({
                "id": e.id,
                "event_type": e.event_type,
                "actor_id": e.actor_id,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "payload": e.payload,
                "timestamp": e.timestamp.isoformat(),
                "previous_hash": e.previous_hash,
                "current_hash": e.current_hash,
                "is_archived": bool(e.is_archived),
                "redacted_fields": e.redacted_fields
            })
            
        return {
            "metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "filters": {"actor_id": actor_id, "resource_id": resource_id}
            },
            "records": records,
            "chain_metadata": {
                "record_count": len(records),
                "verification_instructions": "Verify each record's current_hash matches expected, and sequence is intact where contiguous."
            }
        }
