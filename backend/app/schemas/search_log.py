from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class SearchLogCreate(BaseModel):
    user_id: UUID
    request_id: str
    industry: str
    country: str
    state: str
    city: str
    results_count: int = 0


class SearchLogRead(OrmModel):
    id: UUID
    user_id: UUID
    request_id: str
    industry: str
    country: str
    state: str
    city: str
    results_count: int
    created_at: datetime
