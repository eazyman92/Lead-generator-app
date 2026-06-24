import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test")
os.environ.setdefault("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("AUTH_REFRESH_TOKEN_EXPIRE_DAYS", "30")
os.environ.setdefault("AUTH_JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key")

