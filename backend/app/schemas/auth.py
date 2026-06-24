from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AuthRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=12)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize and validate an email address without extra dependencies."""
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email format.")
        return normalized


class AuthLoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize and validate an email address without extra dependencies."""
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email format.")
        return normalized


class AuthUserResponse(BaseModel):
    id: UUID
    email: str
    role: str


class AuthDataResponse(BaseModel):
    user: AuthUserResponse
