import json
import uuid
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.verification_service import VerificationService
from app.schemas.audit import AuditEventCreate, EventType
from scripts.tamper_database import tamper_record

def run_demo():
    print("--- Audit Log Tamper Evidence Demo ---")
    
    # 1. Setup a clean demo database
    db_file = "demo_audit.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    repo = AuditRepository(session)
    audit_service = AuditService(repo)
    verification_service = VerificationService(repo)
    
    # 2. Insert valid events
    print("\n1. Generating valid audit chain...")
    for i in range(1, 6):
        event = AuditEventCreate(
            eventType=EventType.DATA_ACCESS,
            actorId=f"user-{i}",
            resourceType="document",
            resourceId=str(uuid.uuid4()),
            payload={"action": "read", "bytes": i * 100}
        )
        audit_service.append_event(event)
        
    # 3. Verify valid chain
    print("\n2. Verifying intact chain...")
    result = verification_service.verify_chain()
    print(f"Status: {result.status.value}")
    assert result.status.value == "INTACT", "Chain should be intact"
    
    # 4. Tamper database
    print("\n3. Tampering with database directly (bypassing application logic)...")
    tamper_record(record_id=3, field="actor_id", new_value="hacker", db_url=db_url)
    
    # 5. Verify tampered chain
    print("\n4. Verifying tampered chain...")
    result = verification_service.verify_chain()
    print(f"Status: {result.status.value}")
    
    if result.status.value == "BROKEN":
        print("Tampering successfully detected!")
        err = result.error
        print(f"  First inconsistent record ID: {err.recordId}")
        print(f"  Violation type: {err.violationType.value}")
        print(f"  Expected Hash: {err.expectedHash}")
        print(f"  Actual Hash:   {err.actualHash}")
    else:
        print("ERROR: Tampering was not detected.")
        
    session.close()
    engine.dispose()
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

if __name__ == "__main__":
    run_demo()
