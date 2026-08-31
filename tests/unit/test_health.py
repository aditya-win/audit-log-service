from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
client.headers.update({"X-API-Key": "super-secret-key-123"})

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}
