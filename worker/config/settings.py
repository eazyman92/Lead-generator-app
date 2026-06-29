from functools import lru_cache
import socket

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    internal_api_token: str
    backend_internal_base_url: str = "http://backend:8000"
    worker_id: str = Field(default_factory=socket.gethostname)
    worker_version: str = "0.1.0"
    worker_run_enabled: bool = True
    worker_poll_interval_seconds: float = 2.0
    worker_idle_backoff_max_seconds: float = 30.0
    worker_backoff_multiplier: float = 2.0
    worker_heartbeat_interval_seconds: float = 30.0
    worker_max_concurrent_jobs: int = 1
    worker_default_retry_delay_seconds: int = 60
    worker_retry_max_delay_seconds: int = 3600
    worker_job_timeout_seconds: int = 300
    worker_http_timeout_seconds: int = 45
    worker_user_agent: str = "LeadGeneratorAppWorker/0.1"
    contact_collection_provider: str = "osm"
    contact_collection_max_limit: int = 50

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
