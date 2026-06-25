from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Business, Contact, DataSource, User
from app.repositories import (
    AuditLogRepository,
    BusinessRepository,
    ContactRepository,
    DataSourceRepository,
    SocialProfileRepository,
)
from app.schemas.search import PaginationRequest, PaginationResponse


@dataclass(frozen=True)
class BusinessDetailResult:
    business: Business
    contacts_count: int
    sources_count: int
    social_profiles_count: int


@dataclass(frozen=True)
class BusinessContactsResult:
    business_id: UUID
    contacts: list[Contact]

    pagination: PaginationResponse


@dataclass(frozen=True)
class BusinessSourcesResult:
    business_id: UUID
    data_sources: list[DataSource]
    pagination: PaginationResponse


class BusinessService:
    """Coordinate V1 business detail workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.businesses = BusinessRepository(session)
        self.contacts = ContactRepository(session)
        self.data_sources = DataSourceRepository(session)
        self.social_profiles = SocialProfileRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def get_detail(
        self,
        business_id: UUID,
        user: User,
        context: Any,
    ) -> BusinessDetailResult:
        """Return one business with related V1 summary counts."""
        business = await self._get_business_or_raise(business_id, user, context)
        contacts_count = await self.contacts.count_by_business_id(business_id)
        sources_count = await self.data_sources.count_by_business_id(business_id)
        social_profiles_count = await self.social_profiles.count_by_business_id(business_id)

        await self.audit_logs.log_event(
            event_type="business_detail_viewed",
            request_id=context.request_id,
            user_id=user.id,
            ip_address=context.ip_address,
            metadata={"business_id": str(business_id)},
        )
        await self.session.commit()

        return BusinessDetailResult(
            business=business,
            contacts_count=contacts_count,
            sources_count=sources_count,
            social_profiles_count=social_profiles_count,
        )

    async def get_contacts(
        self,
        business_id: UUID,
        pagination: PaginationRequest,
        user: User,
        context: Any,
    ) -> BusinessContactsResult:
        """Return paginated public contacts for a business."""
        await self._get_business_or_raise(business_id, user, context)
        total = await self.contacts.count_by_business_id(business_id)
        contacts = await self.contacts.list_by_business_id(
            business_id,
            limit=pagination.per_page,
            offset=pagination.offset,
        )

        await self.audit_logs.log_event(
            event_type="business_contacts_viewed",
            request_id=context.request_id,
            user_id=user.id,
            ip_address=context.ip_address,
            metadata={
                "business_id": str(business_id),
                "page": pagination.page,
                "per_page": pagination.per_page,
                "results_count": total,
            },
        )
        await self.session.commit()

        return BusinessContactsResult(
            business_id=business_id,
            contacts=contacts,
            pagination=PaginationResponse.from_counts(
                page=pagination.page,
                per_page=pagination.per_page,
                total=total,
            ),
        )

    async def get_sources(
        self,
        business_id: UUID,
        pagination: PaginationRequest,
        user: User,
        context: Any,
    ) -> BusinessSourcesResult:
        """Return paginated source attribution for a business."""
        await self._get_business_or_raise(business_id, user, context)
        total = await self.data_sources.count_by_business_id(business_id)
        data_sources = await self.data_sources.list_by_business_id(
            business_id,
            limit=pagination.per_page,
            offset=pagination.offset,
        )

        await self.audit_logs.log_event(
            event_type="business_sources_viewed",
            request_id=context.request_id,
            user_id=user.id,
            ip_address=context.ip_address,
            metadata={
                "business_id": str(business_id),
                "page": pagination.page,
                "per_page": pagination.per_page,
                "results_count": total,
            },
        )
        await self.session.commit()

        return BusinessSourcesResult(
            business_id=business_id,
            data_sources=data_sources,
            pagination=PaginationResponse.from_counts(
                page=pagination.page,
                per_page=pagination.per_page,
                total=total,
            ),
        )

    async def audit_rate_limit_denied(
        self,
        user: User,
        context: Any,
        scope: str,
    ) -> None:
        """Log an authenticated business read rate limit denial."""
        await self.audit_logs.log_event(
            event_type="search_domain_rate_limit_denied",
            request_id=context.request_id,
            user_id=user.id,
            ip_address=context.ip_address,
            metadata={"scope": scope},
        )
        await self.session.commit()

    async def _get_business_or_raise(
        self,
        business_id: UUID,
        user: User,
        context: Any,
    ) -> Business:
        business = await self.businesses.get(business_id)
        if business is not None:
            return business

        await self.audit_logs.log_event(
            event_type="business_not_found",
            request_id=context.request_id,
            user_id=user.id,
            ip_address=context.ip_address,
            metadata={"business_id": str(business_id)},
        )
        await self.session.commit()
        raise NotFoundError("BUSINESS_NOT_FOUND", "Business not found.")
