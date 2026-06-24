from dataclasses import dataclass
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.main import app
from app.services.auth_service import AuthResult, AuthTokens


@dataclass
class FakeUser:
    id: object
    email: str
    role: str
    is_active: bool = True


class FakeAuthService:
    async def register(self, email: str, password: str, context):
        return AuthResult(
            user=FakeUser(id=uuid4(), email=email, role="user"),
            tokens=AuthTokens(
                access_token="access-token",
                refresh_token="refresh-token",
                csrf_token="csrf-token-next",
            ),
        )


def test_register_sets_http_only_auth_cookies() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    client = TestClient(app)
    csrf_response = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_response.cookies.get("csrf_token")

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "USER@example.com", "password": "StrongPass123"},
        cookies={"csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user"]["email"] == "user@example.com"
    assert "access-token" not in response.text
    assert "refresh-token" not in response.text
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie
