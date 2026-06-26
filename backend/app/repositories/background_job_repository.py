from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models import BackgroundJob
from app.repositories.base import BaseRepository


ACTIVE_JOB_STATUSES = {"pending", "running"}
RETRYABLE_ERROR_CODES = {
    "NETWORK_TIMEOUT",
    "DNS_FAILURE",
    "HTTP_429",
    "HTTP_5XX",
    "DB_CONFLICT",
}


class BackgroundJobRepository(BaseRepository[BackgroundJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BackgroundJob)

    async def create_job(
        self,
        job_type: str,
        payload: dict[str, Any],
        max_attempts: int = 3,
    ) -> BackgroundJob:
        """Create an idempotent pending job or return the active duplicate."""
        self._validate_payload_envelope(job_type, payload)
        existing = await self.get_active_by_idempotency_key(
            job_type,
            payload["idempotency_key"],
        )
        if existing is not None:
            if job_type == "contact_collection" and self._needs_payload_repair(
                existing.payload,
                payload,
            ):
                existing.payload = payload
                await self.session.flush()
            return existing

        try:
            return await self.create(
                {
                    "job_type": job_type,
                    "status": "pending",
                    "payload": payload,
                    "attempts": 0,
                    "max_attempts": max_attempts,
                    "locked_at": None,
                    "locked_by": None,
                    "error_message": None,
                }
            )
        except IntegrityError:
            await self.session.rollback()
            duplicate = await self.get_active_by_idempotency_key(
                job_type,
                payload["idempotency_key"],
            )
            if duplicate is not None:
                return duplicate
            raise

    async def get_active_by_idempotency_key(
        self,
        job_type: str,
        idempotency_key: str,
    ) -> BackgroundJob | None:
        """Return a pending or running job with the same idempotency key."""
        statement = select(BackgroundJob).where(
            BackgroundJob.job_type == job_type,
            BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
            BackgroundJob.payload["idempotency_key"].astext == idempotency_key,
        )
        return await self.session.scalar(statement)

    async def list_eligible_pending(self, limit: int = 100) -> list[BackgroundJob]:
        """List pending jobs whose retry delay has elapsed."""
        statement = (
            select(BackgroundJob)
            .where(
                BackgroundJob.status == "pending",
                text("COALESCE((payload->>'dead_letter')::boolean, false) = false"),
                text(
                    "(payload->>'retry_after' IS NULL "
                    "OR (payload->>'retry_after')::timestamptz <= now())"
                ),
            )
            .order_by(BackgroundJob.created_at.asc())
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def claim_next(self, worker_id: str) -> BackgroundJob | None:
        """Atomically claim the next eligible pending job using PostgreSQL row locking."""
        statement = select(BackgroundJob).from_statement(
            text(
                """
                UPDATE background_jobs
                SET status = 'running',
                    locked_at = now(),
                    locked_by = :worker_id,
                    attempts = attempts + 1,
                    updated_at = now()
                WHERE id = (
                    SELECT id
                    FROM background_jobs
                    WHERE status = 'pending'
                      AND COALESCE((payload->>'dead_letter')::boolean, false) = false
                      AND (
                          payload->>'retry_after' IS NULL
                          OR (payload->>'retry_after')::timestamptz <= now()
                      )
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING *
                """
            )
        )
        result = await self.session.execute(statement, {"worker_id": worker_id})
        return result.scalar_one_or_none()

    async def complete_job(self, job_id: UUID, worker_id: str) -> BackgroundJob:
        """Mark a running job as completed and clear lock metadata."""
        job = await self._get_existing(job_id)
        self._require_transition(job, "completed")
        self._require_worker_lock(job, worker_id)
        job.status = "completed"
        job.locked_at = None
        job.locked_by = None
        job.error_message = None
        await self.session.flush()
        return job

    async def fail_job(
        self,
        job_id: UUID,
        worker_id: str,
        error_code: str,
        error_message: str,
        retryable: bool,
        retry_delay_seconds: int = 60,
    ) -> BackgroundJob:
        """Record a sanitized job failure, scheduling retry or terminal failure."""
        job = await self._get_existing(job_id)
        self._require_transition(job, "failed")
        self._require_worker_lock(job, worker_id)

        now = datetime.now(timezone.utc)
        payload = dict(job.payload)
        payload["last_error_code"] = error_code
        payload["last_error_at"] = now.isoformat()
        job.error_message = sanitize_error_message(error_message)

        should_retry = (
            retryable
            and error_code in RETRYABLE_ERROR_CODES
            and job.attempts < job.max_attempts
        )
        if should_retry:
            payload["retry_after"] = (now + timedelta(seconds=retry_delay_seconds)).isoformat()
            payload["dead_letter"] = False
            payload["dead_letter_reason"] = None
            job.status = "pending"
        else:
            payload["retry_after"] = None
            payload["dead_letter"] = True
            payload["dead_letter_reason"] = error_code
            job.status = "failed"

        job.payload = payload
        job.locked_at = None
        job.locked_by = None
        await self.session.flush()
        return job

    async def retry_failed_job(
        self,
        job_id: UUID,
        request_id: str,
    ) -> BackgroundJob:
        """Create a new pending job from a failed or dead-lettered job."""
        original = await self._get_existing(job_id)
        if original.status != "failed":
            raise ConflictError("JOB_NOT_RETRYABLE", "Job is not retryable.")

        payload = dict(original.payload)
        payload["request_id"] = request_id
        payload["idempotency_key"] = f"retry:{original.id}:{request_id}"
        payload["retry_after"] = None
        payload["dead_letter"] = False
        payload["dead_letter_reason"] = None
        payload["cancelled"] = False
        payload["cancelled_reason"] = None
        payload["last_error_code"] = None
        payload["last_error_at"] = None
        payload["retries_job_id"] = str(original.id)

        return await self.create_job(original.job_type, payload, original.max_attempts)

    async def cancel_job(self, job_id: UUID, reason: str) -> BackgroundJob:
        """Cancel a pending or running job without re-queueing it."""
        job = await self._get_existing(job_id)
        if job.status not in {"pending", "running"} or job.payload.get("dead_letter") is True:
            raise ConflictError("JOB_NOT_CANCELLABLE", "Job cannot be cancelled.")

        payload = dict(job.payload)
        payload["cancelled"] = True
        payload["cancelled_reason"] = sanitize_error_message(reason)
        payload["dead_letter"] = False
        payload["dead_letter_reason"] = None
        payload["last_error_code"] = "JOB_CANCELLED"
        payload["last_error_at"] = datetime.now(timezone.utc).isoformat()

        job.status = "failed"
        job.payload = payload
        job.error_message = "JOB_CANCELLED"
        job.locked_at = None
        job.locked_by = None
        await self.session.flush()
        return job

    async def _get_existing(self, job_id: UUID) -> BackgroundJob:
        job = await self.get(job_id)
        if job is None:
            raise NotFoundError("JOB_NOT_FOUND", "Job not found.")
        return job

    def _require_transition(self, job: BackgroundJob, target_status: str) -> None:
        allowed_transitions = {
            ("running", "completed"),
            ("running", "failed"),
            ("running", "pending"),
            ("pending", "failed"),
        }
        if (job.status, target_status) not in allowed_transitions:
            raise ConflictError("INVALID_JOB_TRANSITION", "Job transition is not allowed.")

    def _require_worker_lock(self, job: BackgroundJob, worker_id: str) -> None:
        if job.status == "running" and job.locked_by != worker_id:
            raise ConflictError("JOB_LOCKED_BY_OTHER_WORKER", "Job is locked by another worker.")

    def _validate_payload_envelope(self, job_type: str, payload: dict[str, Any]) -> None:
        required_fields = {
            "schema_version",
            "request_id",
            "created_by_user_id",
            "idempotency_key",
            "retry_after",
            "dead_letter",
            "dead_letter_reason",
            "cancelled",
            "cancelled_reason",
            "last_error_code",
            "last_error_at",
            "data",
        }
        missing_fields = required_fields - set(payload)
        if missing_fields:
            raise ValidationAppError(
                "INVALID_PAYLOAD",
                "Job payload envelope is missing required fields.",
            )
        if job_type == "contact_collection" and not self._has_contact_collection_data(payload):
            raise ValidationAppError(
                "INVALID_PAYLOAD",
                "Contact collection job payload data is required.",
            )

    def _needs_payload_repair(
        self,
        existing_payload: dict[str, Any] | None,
        incoming_payload: dict[str, Any],
    ) -> bool:
        existing_data = (existing_payload or {}).get("data")
        incoming_data = incoming_payload.get("data")
        return not bool(existing_data) and bool(incoming_data)

    def _has_contact_collection_data(self, payload: dict[str, Any]) -> bool:
        data = payload.get("data")
        if not isinstance(data, dict) or not data:
            return False
        if data.get("businesses"):
            return True
        return all(data.get(field) for field in ("query", "location", "category"))


def sanitize_error_message(message: str) -> str:
    """Return bounded, single-line error metadata safe for persistence."""
    sanitized = " ".join(message.split())
    return sanitized[:500]
