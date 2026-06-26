from datetime import datetime, timezone

from fastapi import FastAPI

from config.logging import configure_logging, get_logger
from config.settings import get_settings
from jobs.dispatcher import JobDispatcher
from jobs.executor import WorkerExecutor
from jobs.handlers import default_handlers
from jobs.internal_api import InternalApiClient
from jobs.retry import RetryPolicy

configure_logging()
settings = get_settings()
logger = get_logger(__name__)
executor: WorkerExecutor | None = None

app = FastAPI(
    title="Lead Generator App Worker",
    version="0.1.0",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return worker service health."""
    status = executor.state.health if executor else "healthy"
    return {"status": status}


@app.get("/heartbeat")
async def heartbeat() -> dict[str, object]:
    """Return worker heartbeat details."""
    if executor is None:
        return {"status": "starting"}
    return executor.state.heartbeat(datetime.now(timezone.utc))


@app.on_event("startup")
async def startup() -> None:
    global executor
    logger.info(
        "worker_started",
        extra={
            "request_id": "system",
            "service": "worker",
            "worker_id": settings.worker_id,
        },
    )
    api_client = InternalApiClient(
        base_url=settings.backend_internal_base_url,
        internal_api_token=settings.internal_api_token,
        timeout_seconds=settings.worker_http_timeout_seconds,
    )
    dispatcher = JobDispatcher(default_handlers())
    retry_policy = RetryPolicy(
        base_delay_seconds=settings.worker_default_retry_delay_seconds,
        max_delay_seconds=settings.worker_retry_max_delay_seconds,
        backoff_multiplier=settings.worker_backoff_multiplier,
    )
    executor = WorkerExecutor(settings, api_client, dispatcher, retry_policy)
    if settings.worker_run_enabled:
        await executor.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    if executor is not None:
        await executor.stop()
    logger.info(
        "worker_stopped",
        extra={
            "request_id": "system",
            "service": "worker",
            "worker_id": settings.worker_id,
        },
    )
