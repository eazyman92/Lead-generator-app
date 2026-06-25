from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import parse_access_token
from app.core.exceptions import AppError, AuthorizationError, CsrfError
from app.core.permissions import require_permission, require_role
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
from app.services.settings import get_settings


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    ip_address: str | None
    user_agent: str


@dataclass(frozen=True)
class InternalIdentity:
    role: str = "system_worker"


INTERNAL_PERMISSIONS = {
    "internal:job_create",
    "internal:job_claim",
    "internal:job_complete",
    "internal:job_fail",
    "internal:job_read",
}


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


def require_internal_request_id(request: Request) -> str:
    """Require the documented tracing header for internal APIs."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        raise AppError(400, "REQUEST_ID_REQUIRED", "X-Request-ID header is required.")
    request.state.request_id = request_id
    return request_id


def get_internal_identity(
    request_id: str = Depends(require_internal_request_id),
    internal_token: str | None = Header(default=None, alias="X-Internal-API-Token"),
) -> InternalIdentity:
    """Authenticate an internal service request using INTERNAL_API_TOKEN."""
    if not internal_token:
        raise AppError(401, "INTERNAL_AUTH_REQUIRED", "Internal authentication required.")
    if internal_token != get_settings().internal_api_token:
        raise AppError(403, "INTERNAL_AUTH_FORBIDDEN", "Internal authentication forbidden.")
    return InternalIdentity()


def require_internal_permission(permission: str) -> Callable[[InternalIdentity], InternalIdentity]:
    """Create an internal RBAC dependency for system_worker endpoints."""
    async def dependency(
        identity: InternalIdentity = Depends(get_internal_identity),
    ) -> InternalIdentity:
        if identity.role != "system_worker" or permission not in INTERNAL_PERMISSIONS:
            raise AppError(403, "INTERNAL_PERMISSION_DENIED", "Internal permission denied.")
        return identity

    return dependency


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Provide the authentication service."""
    return AuthService(session)


async def validate_csrf(
    request: Request,
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Validate CSRF for state-changing browser requests."""
    if request.method.upper() in {"GET", "HEAD", "OPTIONS"}:
        return

    cookie_token = request.cookies.get(CSRF_TOKEN_COOKIE)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    session_key = request.cookies.get(REFRESH_TOKEN_COOKIE) or "anonymous"
    try:
        validate_csrf_token(cookie_token, header_token, session_key)
    except CsrfError as exc:
        user_id = await service.get_user_id_for_refresh_token(
            request.cookies.get(REFRESH_TOKEN_COOKIE)
        )
        await service.audit_csrf_failure(
            context,
            user_id=user_id,
            failure_reason=exc.failure_reason,
        )
        raise


async def get_current_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> User:
    """Return the authenticated active user."""
    claims = parse_access_token(request.cookies.get(ACCESS_TOKEN_COOKIE))
    return await service.get_active_user(claims.sub)


def require_roles(*roles: str) -> Callable[[User], User]:
    """Create a dependency requiring one of the provided roles."""
    async def dependency(
        request: Request,
        user: User = Depends(get_current_user),
        context: RequestContext = Depends(get_request_context),
        service: AuthService = Depends(get_auth_service),
    ) -> User:
        try:
            require_role(user, roles)
        except AuthorizationError:
            await service.audit_permission_denied(
                user,
                context,
                required_permission=f"role:{','.join(roles)}",
                endpoint=request.url.path,
            )
            raise
        return user

    return dependency


def require_permissions(*permissions: str) -> Callable[[User], User]:
    """Create a dependency requiring all provided permissions."""
    async def dependency(
        request: Request,
        user: User = Depends(get_current_user),
        context: RequestContext = Depends(get_request_context),
        service: AuthService = Depends(get_auth_service),
    ) -> User:
        try:
            for permission in permissions:
                require_permission(user, permission)
        except AuthorizationError:
            await service.audit_permission_denied(
                user,
                context,
                required_permission=",".join(permissions),
                endpoint=request.url.path,
            )
            raise
        return user

    return dependency
