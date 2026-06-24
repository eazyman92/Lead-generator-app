from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class BackgroundJobCreate(BaseModel):
    job_type: str
    payload: dict[str, Any]
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3


class BackgroundJobRead(OrmModel):
    id: UUID
    job_type: str
    status: str
    payload: dict[str, Any]
    attempts: int
    max_attempts: int
    locked_at: datetime | None
    locked_by: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

