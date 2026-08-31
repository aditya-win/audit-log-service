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
client.headers.update({"X-API-Key": "super-secret-key-123"})

@pytest.fixture(autouse=True)
def clear_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_create_and_retrieve():
    # 1. create
    payload = {
        "eventType": "USER_LOGIN",
        "actorId": "user-123",
        "resourceType": "auth",
        "resourceId": "session-1",
        "payload": {"ip": "127.0.0.1"}
    }
    response = client.post("/audit", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["actorId"] == "user-123"
    assert data["id"] == 1
    
    # 2. retrieve
    response = client.get("/audit/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_filtering_and_pagination():
    # create 15 records
    for i in range(1, 16):
        client.post("/audit", json={
            "eventType": "RECORD_UPDATED" if i % 2 == 0 else "USER_LOGIN",
            "actorId": f"user-{i % 3}",
            "resourceType": "auth",
            "resourceId": f"session-{i}",
            "payload": {"index": i}
        })
    
    # pagination default (page 1, size 10)
    response = client.get("/audit")
    assert response.status_code == 200
    assert len(response.json()) == 10
    
    # pagination (page 2, size 10)
    response = client.get("/audit?page=2&pageSize=10")
    assert response.status_code == 200
    assert len(response.json()) == 5
    
    # filter by actorId
    response = client.get("/audit?actorId=user-1")
    assert response.status_code == 200
    assert all(r["actorId"] == "user-1" for r in response.json())

def test_verification_endpoint():
    client.post("/audit", json={
        "eventType": "USER_LOGIN",
        "actorId": "user-123",
        "resourceType": "auth",
        "resourceId": "session-1",
        "payload": {"ip": "127.0.0.1"}
    })
    
    response = client.get("/audit/verify")
    assert response.status_code == 200
    assert response.json()["status"] == "INTACT"

def test_validation_failures():
    response = client.post("/audit", json={
        "eventType": "INVALID"
    })
    assert response.status_code == 422
    
def test_update_attempt_method_not_allowed():
    response = client.put("/audit/1", json={})
    assert response.status_code == 405

def test_delete_attempt_method_not_allowed():
    response = client.delete("/audit/1")
    assert response.status_code == 405

def test_unauthorized_access():
    unauth_client = TestClient(app)
    # Missing API Key entirely -> FastAPI returns 403 Forbidden
    response = unauth_client.get("/audit/verify")
    assert response.status_code == 403
    
    # Wrong API Key -> Our logic returns 401 Unauthorized
    unauth_client.headers.update({"X-API-Key": "wrong-key"})
    response = unauth_client.post("/audit", json={
        "eventType": "USER_LOGIN",
        "actorId": "hacker",
        "resourceType": "system",
        "resourceId": "system",
        "payload": {}
    })
    assert response.status_code == 401
