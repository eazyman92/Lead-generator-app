from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class JobSnapshot:
    id: str
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    retry_after: str | None
    dead_letter: bool
    dead_letter_reason: str | None
    cancelled: bool
    cancelled_reason: str | None
    last_error_code: str | None
    last_error_at: str | None
    locked_at: str | None
    locked_by: str | None
    error_message: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "JobSnapshot":
        return cls(
            id=str(payload["id"]),
            job_type=payload["job_type"],
            status=payload["status"],
            attempts=int(payload["attempts"]),
            max_attempts=int(payload["max_attempts"]),
            retry_after=payload.get("retry_after"),
            dead_letter=bool(payload.get("dead_letter", False)),
            dead_letter_reason=payload.get("dead_letter_reason"),
            cancelled=bool(payload.get("cancelled", False)),
            cancelled_reason=payload.get("cancelled_reason"),
            last_error_code=payload.get("last_error_code"),
            last_error_at=payload.get("last_error_at"),
            locked_at=payload.get("locked_at"),
            locked_by=payload.get("locked_by"),
            error_message=payload.get("error_message"),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
        )


@dataclass(frozen=True)
class HandlerResult:
    success: bool
    retryable: bool = False
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def completed(cls) -> "HandlerResult":
        return cls(success=True)

    @classmethod
    def failed(cls, error_code: str, error_message: str, retryable: bool) -> "HandlerResult":
        return cls(
            success=False,
            retryable=retryable,
            error_code=error_code,
            error_message=error_message,
        )


@dataclass
class WorkerState:
    worker_id: str
    version: str
    started_at: datetime
    active_job_id: str | None = None
    active_job_type: str | None = None
    health: str = "healthy"
    shutdown_requested: bool = False

    def heartbeat(self, now: datetime) -> dict[str, object]:
        return {
            "worker_id": self.worker_id,
            "active_job": self.active_job_id,
            "active_job_type": self.active_job_type,
            "uptime_seconds": int((now - self.started_at).total_seconds()),
            "version": self.version,
            "health": self.health,
            "shutdown_requested": self.shutdown_requested,
        }
