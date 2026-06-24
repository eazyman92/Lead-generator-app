from typing import Any

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import (
    RequestContext,
    get_auth_service,
    get_current_user,
    get_request_context,
    validate_csrf,
)
from app.core.security import (
    ACCESS_TOKEN_COOKIE,
    CSRF_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
    generate_csrf_token,
    get_cookie_settings,
)
from app.models import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest
from app.services.auth_service import AuthResult, AuthService, AuthTokens

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def success_response(
    data: dict[str, Any],
    request_id: str,
    message: str | None = None,
) -> dict[str, Any]:
    """Return the standard API success envelope."""
    return {
        "success": True,
        "data": data,
        "message": message,
        "request_id": request_id,
    }


def user_payload(user: User) -> dict[str, Any]:
    """Return the public user response payload."""
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
    }


@router.post("/register", dependencies=[Depends(validate_csrf)])
async def register(
    payload: AuthRegisterRequest,
    response: Response,
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Register a user and set authentication cookies."""
    result = await service.register(payload.email, payload.password, context)
    set_auth_cookies(response, result)
    return success_response({"user": user_payload(result.user)}, context.request_id)


@router.post("/login", dependencies=[Depends(validate_csrf)])
async def login(
    payload: AuthLoginRequest,
    response: Response,
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Authenticate a user and set authentication cookies."""
    result = await service.login(payload.email, payload.password, context)
    set_auth_cookies(response, result)
    return success_response({"user": user_payload(result.user)}, context.request_id)


@router.post("/refresh", dependencies=[Depends(validate_csrf)])
async def refresh(
    request: Request,
    response: Response,
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Rotate refresh token cookies."""
    tokens = await service.refresh(request.cookies.get(REFRESH_TOKEN_COOKIE), context)
    set_token_cookies(response, tokens)
    return success_response({}, context.request_id)


@router.post("/logout", dependencies=[Depends(validate_csrf)])
async def logout(
    request: Request,
    response: Response,
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Log out the current browser session."""
    await service.logout(request.cookies.get(REFRESH_TOKEN_COOKIE), context)
    clear_auth_cookies(response)
    return success_response({}, context.request_id)


@router.post("/logout-all", dependencies=[Depends(validate_csrf)])
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Log out all active sessions for the current user."""
    await service.logout_all(user, context)
    clear_auth_cookies(response)
    return success_response({}, context.request_id)


@router.get("/me")
async def me(
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Return the current authenticated user."""
    await service.audit_account_access(user, context)
    return success_response({"user": user_payload(user)}, context.request_id)


@router.get("/csrf")
async def csrf(
    request: Request,
    response: Response,
    context: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Set or refresh the CSRF cookie."""
    session_key = request.cookies.get(REFRESH_TOKEN_COOKIE) or "anonymous"
    set_csrf_cookie(response, generate_csrf_token(session_key))
    return success_response({}, context.request_id)


def set_auth_cookies(response: Response, result: AuthResult) -> None:
    """Set access, refresh, and CSRF cookies."""
    set_token_cookies(response, result.tokens)


def set_token_cookies(response: Response, tokens: AuthTokens) -> None:
    """Set token cookies."""
    cookie_settings = get_cookie_settings()
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        tokens.access_token,
        httponly=True,
        secure=cookie_settings.secure,
        samesite=cookie_settings.samesite,
        domain=cookie_settings.domain,
        path=cookie_settings.path,
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE,
        tokens.refresh_token,
        httponly=True,
        secure=cookie_settings.secure,
        samesite=cookie_settings.samesite,
        domain=cookie_settings.domain,
        path=cookie_settings.path,
    )
    set_csrf_cookie(response, tokens.csrf_token)


def set_csrf_cookie(response: Response, csrf_token: str) -> None:
    """Set the readable CSRF cookie."""
    cookie_settings = get_cookie_settings()
    response.set_cookie(
        CSRF_TOKEN_COOKIE,
        csrf_token,
        httponly=False,
        secure=cookie_settings.secure,
        samesite=cookie_settings.samesite,
        domain=cookie_settings.domain,
        path=cookie_settings.path,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication and CSRF cookies."""
    cookie_settings = get_cookie_settings()
    for cookie_name in (ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, CSRF_TOKEN_COOKIE):
        response.delete_cookie(
            cookie_name,
            domain=cookie_settings.domain,
            path=cookie_settings.path,
        )
