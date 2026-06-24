import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test")
os.environ.setdefault("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("AUTH_REFRESH_TOKEN_EXPIRE_DAYS", "30")
os.environ.setdefault("AUTH_JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key")

from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
