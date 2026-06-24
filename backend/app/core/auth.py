from dataclasses import dataclass
from uuid import UUID

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token


@dataclass(frozen=True)
class AccessTokenClaims:
    sub: UUID
    email: str
    role: str
    jti: str


def parse_access_token(token: str | None) -> AccessTokenClaims:
    """Validate an access token and return typed claims."""
    if not token:
        raise AuthenticationError()

    payload = decode_access_token(token)
    try:
        subject = UUID(str(payload["sub"]))
    except ValueError as exc:
        raise AuthenticationError("INVALID_ACCESS_TOKEN", "Invalid access token.") from exc

    return AccessTokenClaims(
        sub=subject,
        email=str(payload["email"]),
        role=str(payload["role"]),
        jti=str(payload["jti"]),
    )
