from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class ExportCreate(BaseModel):
    user_id: UUID
    filters: dict[str, Any]
    format: str = "csv"
    status: str = "pending"
    file_path: str | None = None


class ExportRead(OrmModel):
    id: UUID
    user_id: UUID
    format: str
    filters: dict[str, Any]
    status: str
    file_path: str | None
    created_at: datetime
    updated_at: datetime

