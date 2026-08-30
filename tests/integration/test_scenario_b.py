import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.dependencies import get_db, engine
from app.models.base import Base
from app.models.audit_event import AuditEvent

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def setup_data():
    for i in range(1, 4):
        client.post("/audit", json={
            "eventType": "USER_LOGIN",
            "actorId": f"user-{i}",
            "resourceType": "auth",
            "resourceId": f"session-{i}",
            "payload": {"ip": f"10.0.0.{i}", "secret_token": f"xyz{i}"}
        })

def test_retention_archival():
    setup_data()
    
    # Archive record 2
    response = client.post("/audit/2/archive")
    assert response.status_code == 204
    
    # Retrieve it
    response = client.get("/audit/2")
    data = response.json()
    assert data["isArchived"] is True
    assert data["payload"] == {"_archived": True}
    
    # Verify chain is still INTACT!
    v_res = client.get("/audit/verify")
    assert v_res.json()["status"] == "INTACT"

def test_structured_redaction():
    setup_data()
    
    # Redact secret_token from record 1
    response = client.post("/audit/1/redact", json=["secret_token"])
    assert response.status_code == 200
    
    # Retrieve it
    response = client.get("/audit/1")
    data = response.json()
    assert data["payload"]["secret_token"] == "<REDACTED>"
    assert "secret_token" in data["redactedFields"]
    
    # Verify chain is still INTACT!
    v_res = client.get("/audit/verify")
    assert v_res.json()["status"] == "INTACT"

def test_bulk_export():
    setup_data()
    
    response = client.get("/audit/export/bundle?actorId=user-1")
    assert response.status_code == 200
    data = response.json()
    
    assert "metadata" in data
    assert "records" in data
    assert "chain_metadata" in data
    
    assert len(data["records"]) == 1
    assert data["records"][0]["actor_id"] == "user-1"
