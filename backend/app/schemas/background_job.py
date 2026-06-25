from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import OrmModel

JobType = Literal["contact_collection", "csv_export", "expired_refresh_token_cleanup"]
JobStatus = Literal["pending", "running", "completed", "failed"]


def empty_payload_envelope(
    request_id: str,
    idempotency_key: str,
    data: dict[str, Any],
    created_by_user_id: UUID | None = None,
) -> dict[str, Any]:
    """Build the canonical Phase 4A job payload envelope."""
    return {
        "schema_version": 1,
        "request_id": request_id,
        "created_by_user_id": str(created_by_user_id) if created_by_user_id else None,
        "idempotency_key": idempotency_key,
        "retry_after": None,
        "dead_letter": False,
        "dead_letter_reason": None,
        "cancelled": False,
        "cancelled_reason": None,
        "source_id": None,
        "last_error_code": None,
        "last_error_at": None,
        "data": data,
    }


class BackgroundJobCreate(BaseModel):
    job_type: JobType
    payload: dict[str, Any]
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3


class BackgroundJobRead(OrmModel):
    id: UUID
    job_type: JobType
    status: JobStatus
    payload: dict[str, Any]
    attempts: int
    max_attempts: int
    locked_at: datetime | None
    locked_by: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class InternalJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_type: JobType
    idempotency_key: str = Field(min_length=8, max_length=255)
    data: dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: UUID | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("idempotency_key is required")
        return normalized


class InternalJobClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)


class InternalJobCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)


class InternalJobFailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)
    error_code: str = Field(min_length=2, max_length=64)
    error_message: str = Field(min_length=1, max_length=500)
    retryable: bool = False
    retry_delay_seconds: int = Field(default=60, ge=1, le=86400)


class InternalJobStatusResponse(BaseModel):
    id: UUID
    job_type: JobType
    status: JobStatus
    attempts: int
    max_attempts: int
    retry_after: str | None
    dead_letter: bool
    dead_letter_reason: str | None
    cancelled: bool
    cancelled_reason: str | None
    last_error_code: str | None
    last_error_at: str | None
    locked_at: datetime | None
    locked_by: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_job(cls, job) -> "InternalJobStatusResponse":
        payload = job.payload or {}
        return cls(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            retry_after=payload.get("retry_after"),
            dead_letter=bool(payload.get("dead_letter", False)),
            dead_letter_reason=payload.get("dead_letter_reason"),
            cancelled=bool(payload.get("cancelled", False)),
            cancelled_reason=payload.get("cancelled_reason"),
            last_error_code=payload.get("last_error_code"),
            last_error_at=payload.get("last_error_at"),
            locked_at=job.locked_at,
            locked_by=job.locked_by,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
