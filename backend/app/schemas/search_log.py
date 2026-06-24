from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class SearchLogCreate(BaseModel):
    industry: str
    country: str
    state: str
    city: str
    results_count: int = 0


class SearchLogRead(OrmModel):
    id: UUID
    industry: str
    country: str
    state: str
    city: str
    results_count: int
    created_at: datetime

