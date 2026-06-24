from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class UserCreate(BaseModel):
    email: str
    password_hash: str
    role: str = "user"
    is_active: bool = True


class UserRead(OrmModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

