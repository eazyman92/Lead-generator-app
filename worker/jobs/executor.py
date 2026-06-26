import asyncio
from datetime import datetime, timezone
from time import monotonic

from config.logging import get_logger
from config.settings import Settings
from jobs.dispatcher import JobDispatcher
from jobs.internal_api import InternalApiClient, InternalApiError
from jobs.models import HandlerResult, JobSnapshot, WorkerState
from jobs.retry import RetryPolicy

logger = get_logger(__name__)


class WorkerExecutor:
    def __init__(
        self,
        settings: Settings,
        api_client: InternalApiClient,
        dispatcher: JobDispatcher,
        retry_policy: RetryPolicy,
    ) -> None:
        self.settings = settings
        self.api_client = api_client
        self.dispatcher = dispatcher
        self.retry_policy = retry_policy
        self.state = WorkerState(
            worker_id=settings.worker_id,
            version=settings.worker_version,
            started_at=datetime.now(timezone.utc),
        )
        self._stop_event = asyncio.Event()
        self._loop_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._active_tasks: set[asyncio.Task[None]] = set()

    async def start(self) -> None:
        if self._loop_task is not None:
            return
        self._loop_task = asyncio.create_task(self.poll_loop(), name="worker-poll-loop")
        self._heartbeat_task = asyncio.create_task(
            self.heartbeat_loop(),
            name="worker-heartbeat-loop",
        )

    async def stop(self) -> None:
        self.state.shutdown_requested = True
        self._stop_event.set()
        tasks = [task for task in (self._loop_task, self._heartbeat_task) if task is not None]
        for task in tasks:
            task.cancel()
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def poll_loop(self) -> None:
        idle_delay = self.settings.worker_poll_interval_seconds
        try:
            while not self._stop_event.is_set():
                self._active_tasks = {task for task in self._active_tasks if not task.done()}
                capacity = self.settings.worker_max_concurrent_jobs - len(self._active_tasks)
                claimed = False
                for _ in range(max(capacity, 0)):
                    job = await self.claim_one()
                    if job is None:
                        break
                    claimed = True
                    task = asyncio.create_task(self.process_job(job), name=f"job-{job.id}")
                    self._active_tasks.add(task)

                if claimed:
                    idle_delay = self.settings.worker_poll_interval_seconds
                else:
                    await self._sleep(idle_delay)
                    idle_delay = min(
                        idle_delay * self.settings.worker_backoff_multiplier,
                        self.settings.worker_idle_backoff_max_seconds,
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            self.state.health = "degraded"
            logger.exception(
                "worker_poll_loop_failed",
                extra={"request_id": "system", "worker_id": self.settings.worker_id},
            )

    async def heartbeat_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                await self._sleep(self.settings.worker_heartbeat_interval_seconds)
                logger.info(
                    "worker_heartbeat",
                    extra={
                        "request_id": "system",
                        "worker_id": self.settings.worker_id,
                        **self.state.heartbeat(datetime.now(timezone.utc)),
                    },
                )
        except asyncio.CancelledError:
            raise

    async def claim_one(self) -> JobSnapshot | None:
        try:
            job = await self.api_client.claim_job(self.settings.worker_id)
        except InternalApiError:
            self.state.health = "degraded"
            logger.warning(
                "job_claim_failed",
                extra={
                    "request_id": "system",
                    "worker_id": self.settings.worker_id,
                    "job_id": None,
                    "job_type": None,
                },
            )
            return None

        if job is None:
            return None

        logger.info(
            "job_claimed",
            extra={
                "request_id": "system",
                "worker_id": self.settings.worker_id,
                "job_id": job.id,
                "job_type": job.job_type,
            },
        )
        return job

    async def process_job(self, job: JobSnapshot) -> None:
        self.state.active_job_id = job.id
        self.state.active_job_type = job.job_type
        started = monotonic()
        logger.info(
            "job_started",
            extra={
                "request_id": "system",
                "worker_id": self.settings.worker_id,
                "job_id": job.id,
                "job_type": job.job_type,
            },
        )
        try:
            result = await asyncio.wait_for(
                self.dispatcher.dispatch(job),
                timeout=self.settings.worker_job_timeout_seconds,
            )
            await self.apply_result(job, result, monotonic() - started)
        except TimeoutError:
            await self.apply_result(
                job,
                HandlerResult.failed("NETWORK_TIMEOUT", "Job handler timed out.", True),
                monotonic() - started,
            )
        except Exception as exc:
            await self.apply_result(
                job,
                HandlerResult.failed("UNKNOWN_JOB_TYPE", str(exc), False),
                monotonic() - started,
            )
        finally:
            self.state.active_job_id = None
            self.state.active_job_type = None

    async def apply_result(
        self,
        job: JobSnapshot,
        result: HandlerResult,
        duration_seconds: float,
    ) -> None:
        if result.success:
            completed = await self.api_client.complete_job(job.id, self.settings.worker_id)
            logger.info(
                "job_completed",
                extra=self._job_log_extra(completed, duration_seconds),
            )
            return

        delay = self.retry_policy.delay_for_attempt(job.attempts)
        failed = await self.api_client.fail_job(
            job_id=job.id,
            worker_id=self.settings.worker_id,
            error_code=result.error_code or "UNKNOWN_JOB_TYPE",
            error_message=result.error_message or "Job failed.",
            retryable=result.retryable,
            retry_delay_seconds=delay,
        )
        if failed.status == "pending":
            logger.info(
                "job_retried",
                extra=self._job_log_extra(failed, duration_seconds),
            )
        elif failed.dead_letter:
            logger.warning(
                "job_dead_lettered",
                extra=self._job_log_extra(failed, duration_seconds),
            )
        else:
            logger.warning(
                "job_failed",
                extra=self._job_log_extra(failed, duration_seconds),
            )

    def _job_log_extra(self, job: JobSnapshot, duration_seconds: float) -> dict[str, object]:
        return {
            "request_id": "system",
            "worker_id": self.settings.worker_id,
            "job_id": job.id,
            "job_type": job.job_type,
            "duration_seconds": round(duration_seconds, 3),
        }

    async def _sleep(self, delay: float) -> None:
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
        except TimeoutError:
            return
