from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel


class SocialProfileCreate(BaseModel):
    business_id: UUID
    platform: str
    url: str


class SocialProfileRead(OrmModel):
    id: UUID
    business_id: UUID
    platform: str
    url: str

