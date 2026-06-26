import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from jobs.dispatcher import JobDispatcher
from jobs.executor import WorkerExecutor
from jobs.models import HandlerResult, JobSnapshot
from jobs.retry import RetryPolicy


def build_settings() -> SimpleNamespace:
    return SimpleNamespace(
        worker_id="worker-1",
        worker_version="test",
        worker_poll_interval_seconds=0.01,
        worker_idle_backoff_max_seconds=0.02,
        worker_backoff_multiplier=2,
        worker_heartbeat_interval_seconds=0.01,
        worker_max_concurrent_jobs=1,
        worker_default_retry_delay_seconds=1,
        worker_retry_max_delay_seconds=10,
        worker_job_timeout_seconds=1,
    )


def build_job(attempts: int = 1, status: str = "running") -> JobSnapshot:
    now = datetime.now(timezone.utc).isoformat()
    return JobSnapshot(
        id="job-1",
        job_type="contact_collection",
        status=status,
        attempts=attempts,
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


class FakeApiClient:
    def __init__(self, job: JobSnapshot | None = None) -> None:
        self.job = job
        self.completed = []
        self.failed = []
        self.claims = 0

    async def claim_job(self, worker_id):
        self.claims += 1
        job = self.job
        self.job = None
        return job

    async def complete_job(self, job_id, worker_id):
        self.completed.append({"job_id": job_id, "worker_id": worker_id})
        return build_job(status="completed")

    async def fail_job(
        self,
        job_id,
        worker_id,
        error_code,
        error_message,
        retryable,
        retry_delay_seconds,
    ):
        self.failed.append(
            {
                "job_id": job_id,
                "error_code": error_code,
                "retryable": retryable,
                "retry_delay_seconds": retry_delay_seconds,
            }
        )
        if retryable:
            return build_job(status="pending")
        job = build_job(status="failed")
        return JobSnapshot(
            **{
                **job.__dict__,
                "dead_letter": True,
                "dead_letter_reason": error_code,
            }
        )


class StaticHandler:
    def __init__(self, result: HandlerResult) -> None:
        self.result = result

    async def handle(self, job):
        return self.result


def build_executor(api_client: FakeApiClient, result: HandlerResult) -> WorkerExecutor:
    settings = build_settings()
    dispatcher = JobDispatcher({"contact_collection": StaticHandler(result)})
    retry_policy = RetryPolicy(1, 10, 2)
    return WorkerExecutor(settings, api_client, dispatcher, retry_policy)


def test_executor_claims_and_completes_successful_job() -> None:
    api_client = FakeApiClient(build_job())
    executor = build_executor(api_client, HandlerResult.completed())

    asyncio.run(executor.process_job(build_job()))

    assert api_client.completed == [{"job_id": "job-1", "worker_id": "worker-1"}]
    assert api_client.failed == []


def test_executor_schedules_retry_for_retryable_failure() -> None:
    api_client = FakeApiClient(build_job(attempts=2))
    executor = build_executor(
        api_client,
        HandlerResult.failed("NETWORK_TIMEOUT", "timeout", retryable=True),
    )

    asyncio.run(executor.process_job(build_job(attempts=2)))

    assert api_client.failed[0]["retryable"] is True
    assert api_client.failed[0]["retry_delay_seconds"] == 2


def test_executor_dead_letters_non_retryable_failure() -> None:
    api_client = FakeApiClient(build_job())
    executor = build_executor(
        api_client,
        HandlerResult.failed("INVALID_PAYLOAD", "invalid", retryable=False),
    )

    asyncio.run(executor.process_job(build_job()))

    assert api_client.failed[0]["retryable"] is False
    assert api_client.completed == []


def test_executor_start_and_stop_gracefully_when_idle() -> None:
    async def scenario():
        api_client = FakeApiClient(None)
        executor = build_executor(api_client, HandlerResult.completed())
        await executor.start()
        await asyncio.sleep(0.03)
        await executor.stop()
        assert executor.state.shutdown_requested is True

    asyncio.run(scenario())
