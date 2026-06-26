from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Business, SearchLog, User
from app.repositories import (
    AuditLogRepository,
    BackgroundJobRepository,
    BusinessRepository,
    SearchLogRepository,
)
from app.schemas.background_job import empty_payload_envelope
from app.schemas.search import BusinessSearchRequest, PaginationRequest, PaginationResponse


@dataclass(frozen=True)
class SearchResults:
    businesses: list[Business]
    pagination: PaginationResponse
    job_id: str | None = None


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
        self.background_jobs = BackgroundJobRepository(session)
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
        job_id: str | None = None
        idempotency_key = (
            "contact_collection:search:"
            f"{user.id}:{filters.industry}:{filters.country}:{filters.state}:{filters.city}"
        ).lower()
        latest_job = await self.background_jobs.get_latest_by_idempotency_key(
            "contact_collection",
            idempotency_key,
        )
        should_enqueue_collection = total == 0 and (
            latest_job is None or latest_job.status != "completed"
        )
        if should_enqueue_collection:
            job = await self.background_jobs.create_job(
                "contact_collection",
                empty_payload_envelope(
                    request_id=context.request_id,
                    idempotency_key=idempotency_key,
                    created_by_user_id=user.id,
                    data={
                        "search_id": context.request_id,
                        "query": filters.industry,
                        "category": filters.industry,
                        "location": f"{filters.city}, {filters.state}, {filters.country}",
                        "country": filters.country,
                        "state": filters.state,
                        "city": filters.city,
                        "limit": pagination.per_page,
                        "user_id": str(user.id),
                        "idempotency_key": idempotency_key,
                    },
                ),
            )
            job_id = str(job.id)
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
        if job_id is not None:
            await self._audit(
                "background_job_created",
                user,
                context,
                {
                    "job_id": job_id,
                    "job_type": "contact_collection",
                    "idempotency_key": idempotency_key,
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
            job_id=job_id,
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
