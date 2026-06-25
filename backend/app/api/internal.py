from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import context_success_response
from app.core.dependencies import (
    InternalIdentity,
    RequestContext,
    get_request_context,
    require_internal_permission,
)
from app.repositories.database import get_session
from app.schemas.background_job import (
    InternalJobClaimRequest,
    InternalJobCompleteRequest,
    InternalJobCreateRequest,
    InternalJobFailRequest,
    InternalJobStatusResponse,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/internal/v1", tags=["internal-jobs"])


def get_job_service(session: AsyncSession = Depends(get_session)) -> JobService:
    """Provide the background job service."""
    return JobService(session)


@router.post("/jobs")
async def create_job(
    payload: InternalJobCreateRequest,
    _: InternalIdentity = Depends(require_internal_permission("internal:job_create")),
    context: RequestContext = Depends(get_request_context),
    service: JobService = Depends(get_job_service),
) -> dict[str, object]:
    """Create or return an active idempotent background job."""
    job = await service.create_job(payload, context)
    data = InternalJobStatusResponse.from_job(job).model_dump(mode="json")
    return context_success_response({"job": data}, context)


@router.post("/jobs/claim")
async def claim_job(
    payload: InternalJobClaimRequest,
    _: InternalIdentity = Depends(require_internal_permission("internal:job_claim")),
    context: RequestContext = Depends(get_request_context),
    service: JobService = Depends(get_job_service),
) -> dict[str, object]:
    """Atomically claim the next eligible pending job."""
    job = await service.claim_next_job(payload.worker_id, context)
    data = InternalJobStatusResponse.from_job(job).model_dump(mode="json") if job else None
    return context_success_response({"job": data}, context)


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: UUID,
    _: InternalIdentity = Depends(require_internal_permission("internal:job_read")),
    context: RequestContext = Depends(get_request_context),
    service: JobService = Depends(get_job_service),
) -> dict[str, object]:
    """Return sanitized job status metadata."""
    job = await service.get_job(job_id, context)
    data = InternalJobStatusResponse.from_job(job).model_dump(mode="json")
    return context_success_response({"job": data}, context)


@router.post("/jobs/{job_id}/complete")
async def complete_job(
    job_id: UUID,
    payload: InternalJobCompleteRequest,
    _: InternalIdentity = Depends(require_internal_permission("internal:job_complete")),
    context: RequestContext = Depends(get_request_context),
    service: JobService = Depends(get_job_service),
) -> dict[str, object]:
    """Mark a running job as completed."""
    job = await service.complete_job(job_id, payload.worker_id, context)
    data = InternalJobStatusResponse.from_job(job).model_dump(mode="json")
    return context_success_response({"job": data}, context)


@router.post("/jobs/{job_id}/fail")
async def fail_job(
    job_id: UUID,
    payload: InternalJobFailRequest,
    _: InternalIdentity = Depends(require_internal_permission("internal:job_fail")),
    context: RequestContext = Depends(get_request_context),
    service: JobService = Depends(get_job_service),
) -> dict[str, object]:
    """Fail a running job and schedule retry when allowed."""
    job = await service.fail_job(
        job_id=job_id,
        worker_id=payload.worker_id,
        error_code=payload.error_code,
        error_message=payload.error_message,
        retryable=payload.retryable,
        retry_delay_seconds=payload.retry_delay_seconds,
        context=context,
    )
    data = InternalJobStatusResponse.from_job(job).model_dump(mode="json")
    return context_success_response({"job": data}, context)
