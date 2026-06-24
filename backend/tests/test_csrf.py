from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.main import app


class UnusedAuthService:
    def __init__(self) -> None:
        self.csrf_failures = []

    async def get_user_id_for_refresh_token(self, refresh_token):
        return None

    async def audit_csrf_failure(
        self,
        context,
        user_id=None,
        failure_reason="csrf_validation_failed",
    ):
        self.csrf_failures.append(
            {
                "event_type": "csrf_validation_failure",
                "user_id": user_id,
                "request_id": context.request_id,
                "ip_address": context.ip_address,
                "failure_reason": failure_reason,
            }
        )

    async def login(self, email: str, password: str, context):
        raise AssertionError("CSRF should reject before service is called")


def test_csrf_endpoint_sets_readable_cookie() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/auth/csrf")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "csrf_token=" in response.headers.get("set-cookie", "")
    assert "HttpOnly" not in response.headers.get("set-cookie", "")


def test_state_changing_auth_endpoint_requires_csrf_header() -> None:
    service = UnusedAuthService()
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"
    assert service.csrf_failures == [
        {
            "event_type": "csrf_validation_failure",
            "user_id": None,
            "request_id": response.json()["request_id"],
            "ip_address": "testclient",
            "failure_reason": "missing_csrf_token",
        }
    ]
