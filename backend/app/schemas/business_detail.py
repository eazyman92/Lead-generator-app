from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmModel
from app.schemas.search import PaginationResponse


class BusinessDetailContact(OrmModel):
    id: UUID
    source_id: UUID
    full_name: str
    role: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    is_decision_maker: bool
    priority_score: int
    source_url: str
    collection_timestamp: datetime
    created_at: datetime


class BusinessDetailSource(OrmModel):
    id: UUID
    source_type: str
    source_url: str
    trust_tier: str
    confidence_score: int
    collected_at: datetime


class BusinessDetailSocialProfile(OrmModel):
    id: UUID
    platform: str
    url: str


class BusinessDetailBusiness(OrmModel):
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
    contacts_count: int = 0
    sources_count: int = 0
    social_profiles_count: int = 0


class BusinessDetailData(BaseModel):
    business: BusinessDetailBusiness


class BusinessContactsData(BaseModel):
    business_id: UUID
    contacts: list[BusinessDetailContact]

    pagination: PaginationResponse


class BusinessSourcesData(BaseModel):
    business_id: UUID
    sources: list[BusinessDetailSource]
    pagination: PaginationResponse
