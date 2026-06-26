import os
import sys
from pathlib import Path

WORKER_ROOT = Path(__file__).resolve().parents[1]
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")
os.environ.setdefault("BACKEND_INTERNAL_BASE_URL", "http://backend:8000")
os.environ.setdefault("WORKER_ID", "test-worker")
os.environ.setdefault("WORKER_VERSION", "test-version")
os.environ.setdefault("WORKER_RUN_ENABLED", "false")
os.environ.setdefault("WORKER_POLL_INTERVAL_SECONDS", "0.01")
os.environ.setdefault("WORKER_IDLE_BACKOFF_MAX_SECONDS", "0.02")
os.environ.setdefault("WORKER_BACKOFF_MULTIPLIER", "2")
os.environ.setdefault("WORKER_HEARTBEAT_INTERVAL_SECONDS", "0.01")
os.environ.setdefault("WORKER_MAX_CONCURRENT_JOBS", "1")
os.environ.setdefault("WORKER_DEFAULT_RETRY_DELAY_SECONDS", "1")
os.environ.setdefault("WORKER_RETRY_MAX_DELAY_SECONDS", "10")
os.environ.setdefault("WORKER_JOB_TIMEOUT_SECONDS", "1")
os.environ.setdefault("WORKER_HTTP_TIMEOUT_SECONDS", "1")
