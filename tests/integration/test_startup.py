from fastapi.testclient import TestClient
from app.main import app

def test_app_startup():
    """Verify that the FastAPI application initializes correctly with its configuration."""
    assert app.title == "Audit Log Service"
    assert app.openapi_url == "/openapi.json"
