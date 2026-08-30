import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from app.schemas.audit import AuditEventCreate, EventType, AuditEventQuery

def test_audit_event_create_valid():
    data = {
        "eventType": "USER_LOGIN",
        "actorId": "user-123",
        "resourceType": "system",
        "resourceId": "auth",
        "payload": {"ip": "127.0.0.1"}
    }
    event = AuditEventCreate(**data)
    assert event.eventType == EventType.USER_LOGIN
    assert event.actorId == "user-123"

def test_audit_event_create_missing_fields():
    with pytest.raises(ValidationError):
        AuditEventCreate(eventType="USER_LOGIN")

def test_audit_event_create_invalid_event_type():
    data = {
        "eventType": "UNKNOWN_EVENT",
        "actorId": "user-123",
        "resourceType": "system",
        "resourceId": "auth",
        "payload": {}
    }
    with pytest.raises(ValidationError):
        AuditEventCreate(**data)

def test_audit_event_create_oversized_payload():
    data = {
        "eventType": "USER_LOGIN",
        "actorId": "user-123",
        "resourceType": "system",
        "resourceId": "auth",
        "payload": {"data": "x" * 15000}
    }
    with pytest.raises(ValidationError, match="oversized"):
        AuditEventCreate(**data)

def test_audit_query_valid():
    query = AuditEventQuery(page=2, pageSize=50)
    assert query.page == 2
    assert query.pageSize == 50

def test_audit_query_invalid_pagination():
    with pytest.raises(ValidationError):
        AuditEventQuery(page=0, pageSize=10)
    with pytest.raises(ValidationError):
        AuditEventQuery(page=1, pageSize=200)

def test_audit_query_invalid_date_range():
    now = datetime.now()
    future = now + timedelta(days=1)
    
    with pytest.raises(ValidationError, match="'from' date cannot be after 'to' date"):
        AuditEventQuery(**{"from": future, "to": now})

def test_audit_query_valid_date_range():
    now = datetime.now()
    future = now + timedelta(days=1)
    
    query = AuditEventQuery(**{"from": now, "to": future})
    assert query.from_date == now
    assert query.to_date == future
