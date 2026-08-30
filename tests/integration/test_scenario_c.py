import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.schemas.audit import AuditEventCreate, EventType
from scripts.compliance_report import generate_compliance_report

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    repo = AuditRepository(session)
    audit = AuditService(repo)
    
    # Generate some data
    audit.append_event(AuditEventCreate(
        eventType=EventType.DATA_ACCESS,
        actorId="auditor-1",
        resourceType="account",
        resourceId="client-123",
        payload={"action": "view"}
    ))
    audit.append_event(AuditEventCreate(
        eventType=EventType.USER_LOGIN,
        actorId="client-123",
        resourceType="auth",
        resourceId="session",
        payload={}
    ))
    audit.append_event(AuditEventCreate(
        eventType=EventType.DATA_ACCESS,
        actorId="auditor-2",
        resourceType="account",
        resourceId="client-123",
        payload={"action": "export"}
    ))
    audit.append_event(AuditEventCreate(
        eventType=EventType.DATA_ACCESS,
        actorId="auditor-1",
        resourceType="account",
        resourceId="client-999",
        payload={"action": "view"}
    ))
    
    session.commit()
    
    yield session, "sqlite:///:memory:" # We can't really pass in-memory URL to the script because it creates a new DB. 
    # Wait, the script takes a db_url. If we pass sqlite:///:memory:, it will connect to a new empty memory DB!
    # So we need to refactor the script or test to use a temporary file DB.

@pytest.fixture
def temp_db_file(tmp_path):
    db_file = tmp_path / "test_compliance.db"
    db_url = f"sqlite:///{db_file}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    repo = AuditRepository(session)
    audit = AuditService(repo)
    
    # Generate some data
    audit.append_event(AuditEventCreate(
        eventType=EventType.DATA_ACCESS,
        actorId="auditor-1",
        resourceType="account",
        resourceId="client-123",
        payload={"action": "view"}
    ))
    audit.append_event(AuditEventCreate(
        eventType=EventType.USER_LOGIN,
        actorId="client-123",
        resourceType="auth",
        resourceId="session",
        payload={}
    ))
    audit.append_event(AuditEventCreate(
        eventType=EventType.DATA_ACCESS,
        actorId="auditor-2",
        resourceType="account",
        resourceId="client-123",
        payload={"action": "export"}
    ))
    audit.append_event(AuditEventCreate(
        eventType=EventType.DATA_ACCESS,
        actorId="auditor-1",
        resourceType="account",
        resourceId="client-999",
        payload={"action": "view"}
    ))
    
    session.close()
    
    yield db_url

def test_compliance_report_json(temp_db_file):
    report_str = generate_compliance_report("client-123", db_url=temp_db_file, output_format="json")
    report = json.loads(report_str)
    
    assert report["client_id"] == "client-123"
    assert report["chain_integrity"] == "INTACT"
    assert report["total_access_events"] == 2
    assert "auditor-1" in report["access_by_actor"]
    assert "auditor-2" in report["access_by_actor"]
    assert len(report["access_by_actor"]["auditor-1"]) == 1

def test_compliance_report_markdown(temp_db_file):
    report = generate_compliance_report("client-123", db_url=temp_db_file, output_format="markdown")
    
    assert "Compliance Report: Data Access for Client `client-123`" in report
    assert "✅ INTACT" in report
    assert "**Total Access Events:** 2" in report
    assert "Actor: `auditor-1`" in report
    assert "Actor: `auditor-2`" in report
