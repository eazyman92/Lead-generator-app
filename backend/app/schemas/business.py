from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class BusinessCreate(BaseModel):
    name: str
    industry: str
    website: str
    phone: str
    country: str
    state: str
    city: str
    address: str
    source_type: str
    email: str | None = None
    description: str | None = None


class BusinessRead(OrmModel):
    id: UUID
    name: str
    industry: str
    website: str
    phone: str
    email: str | None
    country: str
    state: str
    city: str
    address: str
    description: str | None
    source_type: str
    created_at: datetime
    updated_at: datetime

