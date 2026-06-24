from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.core.exceptions import AuthorizationError
from app.core.permissions import require_role
from app.core.security import create_access_token
from app.main import app


@dataclass
class FakeUser:
    id: UUID
    email: str
    role: str
    is_active: bool = True


class CurrentUserService:
    def __init__(self, user: FakeUser) -> None:
        self.user = user
        self.account_access_logged = False

    async def get_active_user(self, user_id: UUID):
        assert user_id == self.user.id
        return self.user

    async def audit_account_access(self, user, context):
        self.account_access_logged = True


def test_me_returns_current_user_from_access_token() -> None:
    user = FakeUser(id=uuid4(), email="user@example.com", role="user")
    service = CurrentUserService(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)
    access_token = create_access_token(str(user.id), user.email, user.role)

    response = client.get("/api/v1/auth/me", cookies={"access_token": access_token})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["user"]["email"] == user.email
    assert service.account_access_logged is True


def test_rbac_denies_unapproved_role() -> None:
    user = FakeUser(id=uuid4(), email="user@example.com", role="user")

    with pytest.raises(AuthorizationError):
        require_role(user, ["admin"])
