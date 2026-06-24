from dataclasses import dataclass
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.core.exceptions import AuthenticationError
from app.main import app
from app.services.auth_service import AuthResult, AuthTokens


@dataclass
class FakeUser:
    id: object
    email: str
    role: str
    is_active: bool = True


class LoginSuccessService:
    async def login(self, email: str, password: str, context):
        return AuthResult(
            user=FakeUser(id=uuid4(), email=email, role="user"),
            tokens=AuthTokens("access-token", "refresh-token", "csrf-token-next"),
        )


class LoginFailureService:
    async def login(self, email: str, password: str, context):
        raise AuthenticationError("INVALID_CREDENTIALS", "Invalid credentials.")


def get_csrf(client: TestClient) -> str:
    response = client.get("/api/v1/auth/csrf")
    return response.cookies["csrf_token"]


def test_login_returns_user_without_token_body() -> None:
    app.dependency_overrides[get_auth_service] = lambda: LoginSuccessService()
    client = TestClient(app)
    csrf_token = get_csrf(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
        cookies={"csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["user"]["role"] == "user"
    assert "access-token" not in response.text
    assert "refresh-token" not in response.text


def test_login_rejects_invalid_password() -> None:
    app.dependency_overrides[get_auth_service] = lambda: LoginFailureService()
    client = TestClient(app)
    csrf_token = get_csrf(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
        cookies={"csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
