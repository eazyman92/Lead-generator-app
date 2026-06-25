from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Business, SearchLog, User
from app.repositories import AuditLogRepository, BusinessRepository, SearchLogRepository
from app.schemas.search import BusinessSearchRequest, PaginationRequest, PaginationResponse


@dataclass(frozen=True)
class SearchResults:
    businesses: list[Business]
    pagination: PaginationResponse


@dataclass(frozen=True)
class SearchHistoryResults:
    history: list[SearchLog]
    pagination: PaginationResponse


class SearchService:
    """Coordinate V1 business search workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.businesses = BusinessRepository(session)
        self.search_logs = SearchLogRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def search(
        self,
        payload: BusinessSearchRequest,
        user: User,
        context: Any,
    ) -> SearchResults:
        """Search businesses, persist search analytics, and audit the action."""
        filters = payload.filters
        pagination = payload.pagination
        total = await self.businesses.count_search(
            filters.industry,
            filters.country,
            filters.state,
            filters.city,
        )
        businesses = await self.businesses.search(
            filters.industry,
            filters.country,
            filters.state,
            filters.city,
            limit=pagination.per_page,
            offset=pagination.offset,
        )

        await self.search_logs.create(
            {
                "user_id": user.id,
                "request_id": context.request_id,
                "industry": filters.industry,
                "country": filters.country,
                "state": filters.state,
                "city": filters.city,
                "results_count": total,
            }
        )
        await self._audit(
            "business_search",
            user,
            context,
            {
                "industry": filters.industry,
                "country": filters.country,
                "state": filters.state,
                "city": filters.city,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "results_count": total,
            },
        )
        await self.session.commit()

        return SearchResults(
            businesses=businesses,
            pagination=PaginationResponse.from_counts(
                page=pagination.page,
                per_page=pagination.per_page,
                total=total,
            ),
        )

    async def history(
        self,
        pagination: PaginationRequest,
        user: User,
        context: Any,
    ) -> SearchHistoryResults:
        """Return user-scoped search history from the search log table."""
        total = await self.search_logs.count_history(user.id)
        history = await self.search_logs.list_history(
            user.id,
            limit=pagination.per_page,
            offset=pagination.offset,
        )
        await self._audit(
            "search_history_viewed",
            user,
            context,
            {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "results_count": total,
            },
        )
        await self.session.commit()

        return SearchHistoryResults(
            history=history,
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
        scope: str = "search",
    ) -> None:
        """Log an authenticated search-domain rate limit denial."""
        await self._audit(
            "search_domain_rate_limit_denied",
            user,
            context,
            {"scope": scope},
        )
        await self.session.commit()

    async def _audit(
        self,
        event_type: str,
        user: User,
        context: Any,
        metadata: dict[str, Any],
    ) -> None:
        await self.audit_logs.log_event(
            event_type=event_type,
            request_id=context.request_id,
            user_id=user.id,
            ip_address=context.ip_address,
            metadata=metadata,
        )
