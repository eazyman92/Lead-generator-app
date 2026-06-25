from collections.abc import Iterable
from typing import Protocol

from app.core.exceptions import AuthorizationError


class RoleBearingUser(Protocol):
    role: str

SUPPORTED_ROLES = {"admin", "user"}
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "auth:me",
        "auth:logout",
        "auth:logout_all",
        "auth:refresh",
        "business:read",
        "contact:read",
        "export:create",
        "search:create",
        "search:history",
        "source:read",
        "user:read",
        "user:manage",
    },
    "user": {
        "auth:me",
        "auth:logout",
        "auth:logout_all",
        "auth:refresh",
        "business:read",
        "contact:read",
        "export:create",
        "search:create",
        "search:history",
        "source:read",
        "user:read",
    },
}


def assert_supported_role(role: str) -> None:
    """Validate that a role is supported by Phase 2B RBAC."""
    if role not in SUPPORTED_ROLES:
        raise AuthorizationError()


def require_role(user: RoleBearingUser, allowed_roles: Iterable[str]) -> None:
    """Require that a user has one of the allowed roles."""
    assert_supported_role(user.role)
    if user.role not in set(allowed_roles):
        raise AuthorizationError()


def require_permission(user: RoleBearingUser, permission: str) -> None:
    """Require that a user has a named permission."""
    assert_supported_role(user.role)
    if permission not in ROLE_PERMISSIONS[user.role]:
        raise AuthorizationError()
