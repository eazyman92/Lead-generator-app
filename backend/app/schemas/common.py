from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IdSchema(OrmModel):
    id: UUID


class TimestampSchema(OrmModel):
    created_at: datetime
    updated_at: datetime


JsonObject = dict[str, Any]
