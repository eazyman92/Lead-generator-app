from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class AuditLogCreate(BaseModel):
    event_type: str
    request_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    user_id: UUID | None = None
    ip_address: str | None = None


class AuditLogRead(OrmModel):
    id: UUID
    user_id: UUID | None
    event_type: str
    ip_address: str | None
    request_id: str
    metadata: dict[str, Any] = Field(alias="event_metadata")
    created_at: datetime

