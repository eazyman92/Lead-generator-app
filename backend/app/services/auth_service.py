from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_opaque_token,
    hash_password,
    hash_refresh_token,
    utc_now,
    validate_password_policy,
    verify_password,
)
from app.models import RefreshToken, User
from app.repositories import AuditLogRepository, RefreshTokenRepository, UserRepository
from app.services.settings import get_settings


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    csrf_token: str


@dataclass(frozen=True)
class AuthResult:
    user: User
    tokens: AuthTokens


class AuthService:
    """Coordinate V1 authentication workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def register(self, email: str, password: str, context: Any) -> AuthResult:
        """Register a user and issue initial authentication cookies."""
        validate_password_policy(password)
        existing_user = await self.users.get_by_email(email)
        if existing_user is not None:
            await self._audit(
                "registration_failure",
                context,
                metadata={"reason": "duplicate_email"},
            )
            await self.session.commit()
            raise ConflictError("USER_ALREADY_EXISTS", "User already exists.")

        user = await self.users.create(
            {
                "email": email,
                "password_hash": hash_password(password),
                "role": "user",
                "is_active": True,
            }
        )
        tokens = await self._issue_tokens(user, context)
        await self._audit("registration", context, user_id=user.id)
        await self.session.commit()
        return AuthResult(user=user, tokens=tokens)

    async def login(self, email: str, password: str, context: Any) -> AuthResult:
        """Authenticate a user and issue authentication cookies."""
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            await self._audit(
                "login_failure",
                context,
                user_id=user.id if user else None,
                metadata={"reason": "invalid_credentials"},
            )
            await self.session.commit()
            raise AuthenticationError("INVALID_CREDENTIALS", "Invalid credentials.")

        if not user.is_active:
            await self._audit(
                "login_failure",
                context,
                user_id=user.id,
                metadata={"reason": "inactive_user"},
            )
            await self.session.commit()
            raise AuthenticationError("INVALID_CREDENTIALS", "Invalid credentials.")

        tokens = await self._issue_tokens(user, context)
        await self._audit("login_success", context, user_id=user.id)
        await self.session.commit()
        return AuthResult(user=user, tokens=tokens)

    async def refresh(self, refresh_token: str | None, context: Any) -> AuthTokens:
        """Rotate a refresh token and return new cookies."""
        token_record = await self._load_refresh_token(refresh_token)
        now = utc_now()

        if token_record.revoked_at is not None:
            await self.refresh_tokens.revoke_all_active_for_user(token_record.user_id, now)
            await self._audit("token_reuse_attempt", context, user_id=token_record.user_id)
            await self.session.commit()
            raise AuthenticationError(
                "REFRESH_TOKEN_REUSE_DETECTED",
                "Refresh token reuse detected.",
            )

        if token_record.expires_at <= now:
            await self._audit(
                "refresh_failure",
                context,
                user_id=token_record.user_id,
                metadata={"reason": "expired"},
            )
            await self.session.commit()
            raise AuthenticationError("REFRESH_TOKEN_EXPIRED", "Refresh token expired.")

        user = await self.get_active_user(token_record.user_id)
        new_tokens = await self._issue_tokens(user, context)
        new_token_hash = hash_refresh_token(new_tokens.refresh_token)
        new_record = await self.refresh_tokens.get_by_hash(new_token_hash)
        if new_record is None:
            raise AuthenticationError("REFRESH_TOKEN_REQUIRED", "Refresh token required.")

        await self.refresh_tokens.revoke_with_replacement(token_record, now, new_record.id)
        await self._audit("refresh_token_rotation", context, user_id=user.id)
        await self.session.commit()
        return new_tokens

    async def logout(self, refresh_token: str | None, context: Any) -> None:
        """Revoke the current refresh token when present."""
        if not refresh_token:
            await self._audit("logout", context, metadata={"reason": "missing_refresh_token"})
            await self.session.commit()
            return

        token_record = await self.refresh_tokens.get_by_hash(hash_refresh_token(refresh_token))
        user_id = token_record.user_id if token_record else None
        if token_record and token_record.revoked_at is None:
            await self.refresh_tokens.revoke(token_record, utc_now())

        await self._audit("logout", context, user_id=user_id)
        await self.session.commit()

    async def logout_all(self, user: User, context: Any) -> None:
        """Revoke all active refresh tokens for a user."""
        await self.refresh_tokens.revoke_all_active_for_user(user.id, utc_now())
        await self._audit("logout-all", context, user_id=user.id)
        await self.session.commit()

    async def get_active_user(self, user_id: UUID) -> User:
        """Return an active user or raise an authentication error."""
        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("INVALID_ACCESS_TOKEN", "Invalid access token.")
        return user

    async def audit_account_access(self, user: User, context: Any) -> None:
        """Log a current-user account access event."""
        await self._audit("account_access", context, user_id=user.id)
        await self.session.commit()

    async def audit_csrf_failure(
        self,
        context: Any,
        user_id: UUID | None = None,
        failure_reason: str = "csrf_validation_failed",
    ) -> None:
        """Log a CSRF validation failure without recording token values."""
        await self._audit(
            "csrf_validation_failure",
            context,
            user_id=user_id,
            metadata={"failure_reason": failure_reason},
        )
        await self.session.commit()

    async def audit_permission_denied(
        self,
        user: User,
        context: Any,
        required_permission: str,
        endpoint: str,
    ) -> None:
        """Log an RBAC permission denial."""
        await self._audit(
            "permission_denied",
            context,
            user_id=user.id,
            metadata={
                "required_permission": required_permission,
                "endpoint": endpoint,
            },
        )
        await self.session.commit()

    async def get_user_id_for_refresh_token(self, refresh_token: str | None) -> UUID | None:
        """Resolve a refresh token to a user id using only the stored token hash."""
        if not refresh_token:
            return None

        token_record = await self.refresh_tokens.get_by_hash(hash_refresh_token(refresh_token))
        return token_record.user_id if token_record else None

    async def _issue_tokens(self, user: User, context: Any) -> AuthTokens:
        access_token = create_access_token(str(user.id), user.email, user.role)
        refresh_token = generate_opaque_token()
        now = utc_now()
        settings = get_settings()
        expires_at = now + timedelta(days=settings.auth_refresh_token_expire_days)

        await self.refresh_tokens.create(
            {
                "user_id": user.id,
                "token_hash": hash_refresh_token(refresh_token),
                "issued_at": now,
                "expires_at": expires_at,
                "created_ip": context.ip_address or "",
                "user_agent": context.user_agent,
                "last_used_at": now,
            }
        )

        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=generate_csrf_token(refresh_token),
        )

    async def _load_refresh_token(self, refresh_token: str | None) -> RefreshToken:
        if not refresh_token:
            raise AuthenticationError("REFRESH_TOKEN_REQUIRED", "Refresh token required.")

        token_record = await self.refresh_tokens.get_by_hash(hash_refresh_token(refresh_token))
        if token_record is None:
            raise AuthenticationError("INVALID_REFRESH_TOKEN", "Invalid refresh token.")
        return token_record

    async def _audit(
        self,
        event_type: str,
        context: Any,
        user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.audit_logs.log_event(
            event_type=event_type,
            request_id=context.request_id,
            user_id=user_id,
            ip_address=context.ip_address,
            metadata=metadata,
        )
