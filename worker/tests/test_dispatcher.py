import asyncio
from datetime import datetime, timezone

from jobs.dispatcher import JobDispatcher
from jobs.models import HandlerResult, JobSnapshot


def build_job(job_type: str = "contact_collection") -> JobSnapshot:
    now = datetime.now(timezone.utc).isoformat()
    return JobSnapshot(
        id="job-1",
        job_type=job_type,
        status="running",
        attempts=1,
        max_attempts=3,
        retry_after=None,
        dead_letter=False,
        dead_letter_reason=None,
        cancelled=False,
        cancelled_reason=None,
        last_error_code=None,
        last_error_at=None,
        locked_at=now,
        locked_by="worker-1",
        error_message=None,
        created_at=now,
        updated_at=now,
    )


class SuccessHandler:
    async def handle(self, job):
        return HandlerResult.completed()


def test_dispatcher_routes_supported_job_type() -> None:
    dispatcher = JobDispatcher({"contact_collection": SuccessHandler()})

    result = asyncio.run(dispatcher.dispatch(build_job()))

    assert result.success is True


def test_dispatcher_rejects_unknown_job_type() -> None:
    dispatcher = JobDispatcher({})

    result = asyncio.run(dispatcher.dispatch(build_job("unknown")))

    assert result.success is False
    assert result.error_code == "UNKNOWN_JOB_TYPE"
    assert result.retryable is False
