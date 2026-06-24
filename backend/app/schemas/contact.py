from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class ContactCreate(BaseModel):
    business_id: UUID
    full_name: str
    source_url: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    is_decision_maker: bool = False
    priority_score: int = Field(default=0, ge=0, le=100)


class ContactRead(OrmModel):
    id: UUID
    business_id: UUID
    full_name: str
    role: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    is_decision_maker: bool
    priority_score: int
    source_url: str
    created_at: datetime

