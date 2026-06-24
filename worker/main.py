from fastapi import FastAPI

from config.logging import configure_logging, get_logger
from config.settings import get_settings

configure_logging()
settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title="Lead Generator App Worker",
    version="0.1.0",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return worker service health."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup() -> None:
    logger.info("worker_started", extra={"request_id": "system", "service": "worker"})

