from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class RefreshTokenCreate(BaseModel):
    user_id: UUID
    token_hash: str
    issued_at: datetime
    expires_at: datetime
    created_ip: str
    user_agent: str
    last_used_at: datetime
    replaced_by_token_id: UUID | None = None


class RefreshTokenRead(OrmModel):
    id: UUID
    user_id: UUID
    token_hash: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_token_id: UUID | None
    created_ip: str
    user_agent: str
    last_used_at: datetime

