from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import parse_access_token
from app.core.permissions import require_role
from app.core.security import (
    ACCESS_TOKEN_COOKIE,
    CSRF_HEADER_NAME,
    CSRF_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
    validate_csrf_token,
)
from app.models import User
from app.repositories.database import get_session
from app.services.auth_service import AuthService


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    ip_address: str | None
    user_agent: str


def get_request_context(request: Request) -> RequestContext:
    """Build request context for tracing and audit logging."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid4())
        request.state.request_id = request_id

    client_host = request.client.host if request.client else None
    return RequestContext(
        request_id=request_id,
        ip_address=client_host,
        user_agent=request.headers.get("user-agent", ""),
    )


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Provide the authentication service."""
    return AuthService(session)


async def validate_csrf(request: Request) -> None:
    """Validate CSRF for state-changing browser requests."""
    if request.method.upper() in {"GET", "HEAD", "OPTIONS"}:
        return

    cookie_token = request.cookies.get(CSRF_TOKEN_COOKIE)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    session_key = request.cookies.get(REFRESH_TOKEN_COOKIE) or "anonymous"
    validate_csrf_token(cookie_token, header_token, session_key)


async def get_current_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> User:
    """Return the authenticated active user."""
    claims = parse_access_token(request.cookies.get(ACCESS_TOKEN_COOKIE))
    return await service.get_active_user(claims.sub)


def require_roles(*roles: str) -> Callable[[User], User]:
    """Create a dependency requiring one of the provided roles."""
    async def dependency(user: User = Depends(get_current_user)) -> User:
        require_role(user, roles)
        return user

    return dependency
