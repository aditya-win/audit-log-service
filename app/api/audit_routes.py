import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies import get_audit_service, get_verification_service
from app.services.audit_service import AuditService
from app.services.verification_service import VerificationService
from app.schemas.audit import AuditEventCreate, AuditEventResponse, AuditEventQuery
from app.schemas.verification import VerificationResponse

router = APIRouter(prefix="/audit", tags=["Audit"])

def map_event_to_response(event) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        eventType=event.event_type,
        actorId=event.actor_id,
        resourceType=event.resource_type,
        resourceId=event.resource_id,
        payload=json.loads(event.payload),
        timestamp=event.timestamp,
        previousHash=event.previous_hash,
        currentHash=event.current_hash
    )

@router.post("", response_model=AuditEventResponse, status_code=201)
def create_audit_event(
    event_in: AuditEventCreate,
    service: AuditService = Depends(get_audit_service)
):
    event = service.append_event(event_in)
    return map_event_to_response(event)

@router.get("/verify", response_model=VerificationResponse)
def verify_audit_chain(
    service: VerificationService = Depends(get_verification_service)
):
    return service.verify_chain()

@router.get("/{id}", response_model=AuditEventResponse)
def get_audit_event(
    id: int,
    service: AuditService = Depends(get_audit_service)
):
    event = service.get_event(id)
    if not event:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return map_event_to_response(event)

@router.get("", response_model=List[AuditEventResponse])
def get_audit_events(
    query: AuditEventQuery = Depends(),
    service: AuditService = Depends(get_audit_service)
):
    events = service.get_events(query)
    return [map_event_to_response(e) for e in events]
