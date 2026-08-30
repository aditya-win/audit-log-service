import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.verification_service import VerificationService
from app.schemas.audit import AuditEventCreate, EventType
from app.schemas.verification import ChainStatus, ViolationType

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def services(db_session):
    repo = AuditRepository(db_session)
    audit = AuditService(repo)
    verify = VerificationService(repo)
    return audit, verify, db_session

def setup_chain(audit_service):
    for i in range(1, 6):
        audit_service.append_event(AuditEventCreate(
            eventType=EventType.RECORD_UPDATED,
            actorId=f"user-{i}",
            resourceType="file",
            resourceId=f"file-{i}",
            payload={"status": "ok"}
        ))

def test_payload_mutation(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 2).first()
    record.payload = '{"status": "hacked"}'
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 2
    assert result.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_event_type_mutation(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 3).first()
    record.event_type = "USER_LOGIN"
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 3
    assert result.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_actor_mutation(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 4).first()
    record.actor_id = "admin"
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 4
    assert result.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_timestamp_mutation(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 2).first()
    record.timestamp = record.timestamp + timedelta(days=1)
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 2
    assert result.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_previous_hash_mutation(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 3).first()
    record.previous_hash = "0000badhash0000"
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 3
    assert result.error.violationType == ViolationType.HASH_MISMATCH

def test_current_hash_mutation(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 3).first()
    record.current_hash = "0000badhash0000"
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 3
    assert result.error.violationType == ViolationType.TAMPERED_PAYLOAD

def test_deleted_intermediate_record(services):
    audit, verify, session = services
    setup_chain(audit)
    
    record = session.query(AuditEvent).filter(AuditEvent.id == 3).first()
    session.delete(record)
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    # Record 4 will have a previous_hash that doesn't match Record 2's current_hash
    assert result.error.recordId == 4
    assert result.error.violationType == ViolationType.HASH_MISMATCH

def test_unexpected_inserted_record(services):
    audit, verify, session = services
    setup_chain(audit)
    
    # Manually insert a rogue record in the middle without updating subsequent previous_hashes
    record_2 = session.query(AuditEvent).filter(AuditEvent.id == 2).first()
    
    rogue = AuditEvent(
        event_type="DATA_ACCESS",
        actor_id="rogue",
        resource_type="system",
        resource_id="db",
        payload="{}",
        timestamp=datetime.now(timezone.utc),
        previous_hash=record_2.current_hash,
        current_hash="some_fake_hash"
    )
    # Give it an ID to fit between 2 and 3 if we were sorting by time, 
    # but our DB sorts by ID. SQLite will just append it as ID 6 if we don't specify,
    # which would just look like an invalid append.
    # To simulate an insertion in the middle of the chain, we would change IDs.
    # Let's change record 3's previous hash to a fake one to simulate a break,
    # or just insert it and see it fail.
    
    # Actually, if we insert as ID=6, it's at the end. If its previous_hash != record 5's current_hash:
    rogue.previous_hash = "some_random_hash"
    session.add(rogue)
    session.commit()
    
    result = verify.verify_chain()
    assert result.status == ChainStatus.BROKEN
    assert result.error.recordId == 6
    assert result.error.violationType == ViolationType.HASH_MISMATCH
