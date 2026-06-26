from datetime import datetime
from math import ceil
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import OrmModel


def normalize_search_text(value: str) -> str:
    """Normalize user-provided search text without changing display casing."""
    return " ".join(value.strip().split())


class PaginationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Return SQL offset for page-based pagination."""
        return (self.page - 1) * self.per_page


class PaginationResponse(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def from_counts(cls, page: int, per_page: int, total: int) -> "PaginationResponse":
        """Build pagination metadata from page inputs and total rows."""
        total_pages = ceil(total / per_page) if total else 0
        return cls(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1 and total_pages > 0,
        )


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    industry: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)

    @field_validator("industry", "country", "state", "city", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Trim and collapse repeated whitespace in search filters."""
        if not isinstance(value, str):
            return value
        return normalize_search_text(value)


class BusinessSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filters: SearchFilters
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class BusinessSearchResult(OrmModel):
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
    source_type: str


class BusinessSearchData(BaseModel):
    results: list[BusinessSearchResult]
    pagination: PaginationResponse
    job: dict[str, str] | None = None


class SearchHistoryItem(OrmModel):
    id: UUID
    industry: str
    country: str
    state: str
    city: str
    results_count: int
    created_at: datetime


class SearchHistoryData(BaseModel):
    history: list[SearchHistoryItem]
    pagination: PaginationResponse
