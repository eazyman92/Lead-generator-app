import asyncio
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.core.dependencies import RequestContext, require_permissions
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


@dataclass
class FakeRequestUrl:
    path: str


@dataclass
class FakeRequest:
    url: FakeRequestUrl


class PermissionAuditService:
    def __init__(self) -> None:
        self.permission_denials = []

    async def audit_permission_denied(self, user, context, required_permission, endpoint):
        self.permission_denials.append(
            {
                "event_type": "permission_denied",
                "user_id": user.id,
                "request_id": context.request_id,
                "ip_address": context.ip_address,
                "required_permission": required_permission,
                "endpoint": endpoint,
            }
        )


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


def test_permission_denial_is_audited() -> None:
    user = FakeUser(id=uuid4(), email="user@example.com", role="user")
    request = FakeRequest(url=FakeRequestUrl(path="/api/v1/admin/users"))
    context = RequestContext(
        request_id="request-123",
        ip_address="203.0.113.10",
        user_agent="pytest",
    )
    service = PermissionAuditService()
    dependency = require_permissions("user:manage")

    with pytest.raises(AuthorizationError):
        asyncio.run(
            dependency(
                request=request,
                user=user,
                context=context,
                service=service,
            )
        )

    assert service.permission_denials == [
        {
            "event_type": "permission_denied",
            "user_id": user.id,
            "request_id": "request-123",
            "ip_address": "203.0.113.10",
            "required_permission": "user:manage",
            "endpoint": "/api/v1/admin/users",
        }
    ]
