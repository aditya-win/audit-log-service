import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.verification_service import VerificationService
from app.schemas.audit import AuditEventCreate, EventType
from app.schemas.verification import ChainStatus, ViolationType
from app.utils.hashing import GENESIS_HASH

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def audit_service(db_session):
    repo = AuditRepository(db_session)
    return AuditService(repo)

@pytest.fixture
def verification_service(db_session):
    repo = AuditRepository(db_session)
    return VerificationService(repo)

def create_event(idx: int) -> AuditEventCreate:
    return AuditEventCreate(
        eventType=EventType.USER_LOGIN,
        actorId=f"user-{idx}",
        resourceType="auth",
        resourceId=f"session-{idx}",
        payload={"ip": f"192.168.1.{idx}"}
    )

def test_genesis_record(audit_service, db_session):
    event_in = create_event(1)
    record = audit_service.append_event(event_in)
    
    assert record.id == 1
    assert record.previous_hash == GENESIS_HASH
    assert record.current_hash is not None

def test_previous_hash_linking_and_intact_chain(audit_service, verification_service):
    # Create 3 records
    for i in range(1, 4):
        audit_service.append_event(create_event(i))

    response = verification_service.verify_chain()
    assert response.status == ChainStatus.INTACT
    assert response.error is None

def test_payload_modification_detection(audit_service, verification_service, db_session):
    for i in range(1, 4):
        audit_service.append_event(create_event(i))
        
    # Tamper with record 2
    record_2 = db_session.query(AuditEvent).filter(AuditEvent.id == 2).first()
    record_2.payload = '{"ip":"tampered"}'
    db_session.commit()
    
    response = verification_service.verify_chain()
    assert response.status == ChainStatus.BROKEN
    assert response.error.recordId == 2
    assert response.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_field_modification_detection(audit_service, verification_service, db_session):
    for i in range(1, 4):
        audit_service.append_event(create_event(i))
        
    # Tamper with actor_id of record 1
    record_1 = db_session.query(AuditEvent).filter(AuditEvent.id == 1).first()
    record_1.actor_id = "hacker"
    db_session.commit()
    
    response = verification_service.verify_chain()
    assert response.status == ChainStatus.BROKEN
    assert response.error.recordId == 1
    assert response.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_previous_hash_modification_detection(audit_service, verification_service, db_session):
    for i in range(1, 4):
        audit_service.append_event(create_event(i))
        
    # Tamper with previous_hash of record 3
    record_3 = db_session.query(AuditEvent).filter(AuditEvent.id == 3).first()
    record_3.previous_hash = "badhash"
    db_session.commit()
    
    response = verification_service.verify_chain()
    assert response.status == ChainStatus.BROKEN
    assert response.error.recordId == 3
    # Our logic checks previous_hash link first
    assert response.error.violationType == ViolationType.HASH_MISMATCH

def test_deleted_intermediate_record(audit_service, verification_service, db_session):
    for i in range(1, 4):
        audit_service.append_event(create_event(i))
        
    # Delete record 2
    record_2 = db_session.query(AuditEvent).filter(AuditEvent.id == 2).first()
    db_session.delete(record_2)
    db_session.commit()
    
    response = verification_service.verify_chain()
    assert response.status == ChainStatus.BROKEN
    # The chain breaks when verifying record 3 because its previous_hash won't match record 1's current_hash
    assert response.error.recordId == 3
    assert response.error.violationType == ViolationType.HASH_MISMATCH
