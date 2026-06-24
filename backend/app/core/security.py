from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from argon2.low_level import Type

from app.core.exceptions import AuthenticationError, CsrfError, ValidationAppError
from app.services.settings import get_settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
CSRF_TOKEN_COOKIE = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

_password_hasher = PasswordHasher(type=Type.ID)


@dataclass(frozen=True)
class CookieSettings:
    domain: str | None
    secure: bool
    samesite: str
    path: str = "/"


def get_cookie_settings() -> CookieSettings:
    """Return configured cookie settings."""
    settings = get_settings()
    domain = settings.auth_cookie_domain or None
    return CookieSettings(
        domain=domain,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


def validate_password_policy(password: str) -> None:
    """Validate the configured password policy."""
    if len(password) < 12:
        raise ValidationAppError(
            "PASSWORD_POLICY_VIOLATION",
            "Password must be at least 12 characters.",
        )
    if not any(character.isupper() for character in password):
        raise ValidationAppError(
            "PASSWORD_POLICY_VIOLATION",
            "Password must include an uppercase letter.",
        )
    if not any(character.islower() for character in password):
        raise ValidationAppError(
            "PASSWORD_POLICY_VIOLATION",
            "Password must include a lowercase letter.",
        )
    if not any(character.isdigit() for character in password):
        raise ValidationAppError("PASSWORD_POLICY_VIOLATION", "Password must include a number.")


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    now = utc_now()
    expires_at = now + timedelta(minutes=settings.auth_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.auth_jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.auth_jwt_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("ACCESS_TOKEN_EXPIRED", "Access token expired.") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("INVALID_ACCESS_TOKEN", "Invalid access token.") from exc

    if payload.get("type") != "access":
        raise AuthenticationError("INVALID_ACCESS_TOKEN", "Invalid access token.")

    for claim in ("sub", "email", "role", "jti", "iat", "exp"):
        if claim not in payload:
            raise AuthenticationError("INVALID_ACCESS_TOKEN", "Invalid access token.")

    return payload


def generate_opaque_token() -> str:
    """Generate a cryptographically random opaque token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token before storage or lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token(session_key: str = "anonymous") -> str:
    """Generate a signed CSRF token bound to a session key."""
    nonce = secrets.token_urlsafe(32)
    signature = _sign_csrf_nonce(nonce, session_key)
    return f"{nonce}.{signature}"


def validate_csrf_token(
    cookie_token: str | None,
    header_token: str | None,
    session_key: str = "anonymous",
) -> None:
    """Validate a CSRF cookie/header pair."""
    if not cookie_token or not header_token:
        raise CsrfError()
    if not hmac.compare_digest(cookie_token, header_token):
        raise CsrfError()

    try:
        nonce, signature = cookie_token.split(".", 1)
    except ValueError as exc:
        raise CsrfError() from exc

    expected = _sign_csrf_nonce(nonce, session_key)
    if not hmac.compare_digest(signature, expected):
        raise CsrfError()


def _sign_csrf_nonce(nonce: str, session_key: str) -> str:
    settings = get_settings()
    session_digest = hashlib.sha256(session_key.encode("utf-8")).hexdigest()
    digest = hmac.new(
        settings.auth_jwt_secret_key.encode("utf-8"),
        f"{nonce}:{session_digest}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest
