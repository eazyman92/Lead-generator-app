from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.core.exceptions import AuthenticationError
from app.main import app
from app.services.auth_service import AuthTokens


class RefreshSuccessService:
    async def refresh(self, refresh_token: str | None, context):
        assert refresh_token == "old-refresh"
        return AuthTokens("new-access", "new-refresh", "new-csrf")


class RefreshFailureService:
    async def refresh(self, refresh_token: str | None, context):
        raise AuthenticationError("INVALID_REFRESH_TOKEN", "Invalid refresh token.")


def get_csrf(client: TestClient) -> str:
    response = client.get("/api/v1/auth/csrf")
    return response.cookies["csrf_token"]


def test_refresh_rotates_refresh_cookie() -> None:
    app.dependency_overrides[get_auth_service] = lambda: RefreshSuccessService()
    client = TestClient(app)
    csrf_token = get_csrf(client)

    response = client.post(
        "/api/v1/auth/refresh",
        cookies={"csrf_token": csrf_token, "refresh_token": "old-refresh"},
        headers={"X-CSRF-Token": csrf_token},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "new-access" in response.headers.get("set-cookie", "")
    assert "new-refresh" in response.headers.get("set-cookie", "")
    assert "new-access" not in response.text
    assert "new-refresh" not in response.text


def test_refresh_rejects_invalid_token() -> None:
    app.dependency_overrides[get_auth_service] = lambda: RefreshFailureService()
    client = TestClient(app)
    csrf_token = get_csrf(client)

    response = client.post(
        "/api/v1/auth/refresh",
        cookies={"csrf_token": csrf_token, "refresh_token": "bad-refresh"},
        headers={"X-CSRF-Token": csrf_token},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"
