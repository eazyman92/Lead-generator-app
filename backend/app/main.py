from fastapi import FastAPI

from app.api.health import router as health_router
from app.services.logging import configure_logging, get_logger
from app.services.settings import get_settings

configure_logging()
settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title="Lead Generator App API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

app.include_router(health_router)


@app.on_event("startup")
async def startup() -> None:
    logger.info("backend_started", extra={"request_id": "system", "service": "backend"})

