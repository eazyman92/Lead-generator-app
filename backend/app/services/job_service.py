from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackgroundJob
from app.repositories import AuditLogRepository, BackgroundJobRepository
from app.schemas.background_job import InternalJobCreateRequest, empty_payload_envelope


class JobService:
    """Coordinate Phase 4A background job queue foundation workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = BackgroundJobRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_job(self, payload: InternalJobCreateRequest, context: Any) -> BackgroundJob:
        """Create or return an existing active idempotent job."""
        envelope = empty_payload_envelope(
            request_id=context.request_id,
            idempotency_key=payload.idempotency_key,
            data=payload.data,
            created_by_user_id=payload.created_by_user_id,
        )
        job = await self.jobs.create_job(payload.job_type, envelope, payload.max_attempts)
        await self._audit(
            "background_job_created",
            context,
            job,
            metadata={"idempotency_key": payload.idempotency_key},
        )
        await self.session.commit()
        return job

    async def claim_next_job(self, worker_id: str, context: Any) -> BackgroundJob | None:
        """Claim the next eligible job for a worker."""
        job = await self.jobs.claim_next(worker_id)
        if job is not None:
            await self._audit(
                "background_job_claimed",
                context,
                job,
                metadata={"worker_id": worker_id},
            )
        await self.session.commit()
        return job

    async def complete_job(self, job_id: UUID, worker_id: str, context: Any) -> BackgroundJob:
        """Complete a running job."""
        job = await self.jobs.complete_job(job_id, worker_id)
        await self._audit(
            "background_job_completed",
            context,
            job,
            metadata={"worker_id": worker_id},
        )
        await self.session.commit()
        return job

    async def fail_job(
        self,
        job_id: UUID,
        worker_id: str,
        error_code: str,
        error_message: str,
        retryable: bool,
        retry_delay_seconds: int,
        context: Any,
    ) -> BackgroundJob:
        """Fail a running job, scheduling retry when allowed."""
        job = await self.jobs.fail_job(
            job_id=job_id,
            worker_id=worker_id,
            error_code=error_code,
            error_message=error_message,
            retryable=retryable,
            retry_delay_seconds=retry_delay_seconds,
        )
        event_type = (
            "background_job_retry_scheduled"
            if job.status == "pending"
            else "background_job_dead_lettered"
        )
        await self._audit(
            event_type,
            context,
            job,
            metadata={
                "worker_id": worker_id,
                "error_code": error_code,
                "attempts": job.attempts,
                "max_attempts": job.max_attempts,
            },
        )
        if job.status == "failed":
            await self._audit(
                "background_job_failed",
                context,
                job,
                metadata={
                    "worker_id": worker_id,
                    "error_code": error_code,
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                },
            )
        await self.session.commit()
        return job

    async def get_job(self, job_id: UUID, context: Any) -> BackgroundJob:
        """Return a job by id."""
        job = await self.jobs._get_existing(job_id)
        await self._audit("background_job_status_viewed", context, job, metadata={})
        await self.session.commit()
        return job

    async def _audit(
        self,
        event_type: str,
        context: Any,
        job: BackgroundJob,
        metadata: dict[str, Any],
    ) -> None:
        audit_metadata = {
            "job_id": str(job.id),
            "job_type": job.job_type,
            **metadata,
        }
        await self.audit_logs.log_event(
            event_type=event_type,
            request_id=context.request_id,
            user_id=None,
            ip_address=context.ip_address,
            metadata=audit_metadata,
        )
