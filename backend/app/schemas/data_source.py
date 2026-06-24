from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class DataSourceCreate(BaseModel):
    business_id: UUID
    source_type: str
    source_url: str
    trust_tier: str
    confidence_score: int = Field(ge=0, le=100)
    collected_at: datetime


class DataSourceRead(OrmModel):
    id: UUID
    business_id: UUID
    source_type: str
    source_url: str
    trust_tier: str
    confidence_score: int
    collected_at: datetime

