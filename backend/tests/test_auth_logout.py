from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.main import app


class LogoutService:
    def __init__(self) -> None:
        self.seen_refresh_token: str | None = None

    async def logout(self, refresh_token: str | None, context):
        self.seen_refresh_token = refresh_token


def test_logout_revokes_refresh_token_and_clears_cookies() -> None:
    service = LogoutService()
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)
    csrf_response = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_response.cookies["csrf_token"]

    response = client.post(
        "/api/v1/auth/logout",
        cookies={"csrf_token": csrf_token, "refresh_token": "refresh-token"},
        headers={"X-CSRF-Token": csrf_token},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.seen_refresh_token == "refresh-token"
    assert response.json()["success"] is True
    assert "access_token=" in response.headers.get("set-cookie", "")
    assert "refresh_token=" in response.headers.get("set-cookie", "")
