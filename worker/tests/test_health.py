import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")

from fastapi.testclient import TestClient
from main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_heartbeat_endpoint_returns_worker_metadata() -> None:
    client = TestClient(app)

    response = client.get("/heartbeat")

    assert response.status_code == 200
    assert response.json()["worker_id"] == "test-worker"
    assert response.json()["version"] == "test-version"
    assert response.json()["health"] == "healthy"
