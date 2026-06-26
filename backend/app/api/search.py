from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rate_limits import enforce_search_domain_rate_limit
from app.api.responses import context_success_response
from app.core.dependencies import RequestContext, get_request_context, require_permissions, validate_csrf
from app.models import User
from app.repositories.database import get_session
from app.schemas.search import (
    BusinessSearchData,
    BusinessSearchRequest,
    BusinessSearchResult,
    PaginationRequest,
    SearchHistoryData,
    SearchHistoryItem,
)
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])


def get_search_service(session: AsyncSession = Depends(get_session)) -> SearchService:
    """Provide the search service."""
    return SearchService(session)


@router.post("/api/v1/search", dependencies=[Depends(validate_csrf)])
async def search_businesses(
    payload: BusinessSearchRequest,
    user: User = Depends(require_permissions("search:create")),
    context: RequestContext = Depends(get_request_context),
    service: SearchService = Depends(get_search_service),
) -> dict[str, object]:
    """Search businesses by industry and location."""
    await enforce_search_domain_rate_limit(user, context, service, "search")
    result = await service.search(payload, user, context)
    data = BusinessSearchData(
        results=[BusinessSearchResult.model_validate(business) for business in result.businesses],
        pagination=result.pagination,
        job={"id": result.job_id, "type": "contact_collection"} if result.job_id else None,
    )
    return context_success_response(data.model_dump(mode="json"), context)


@router.get("/api/v1/search/history")
async def search_history(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permissions("search:history")),
    context: RequestContext = Depends(get_request_context),
    service: SearchService = Depends(get_search_service),
) -> dict[str, object]:
    """Return paginated search history."""
    await enforce_search_domain_rate_limit(user, context, service, "search_history")
    pagination = PaginationRequest(page=page, per_page=per_page)
    result = await service.history(pagination, user, context)
    data = SearchHistoryData(
        history=[SearchHistoryItem.model_validate(item) for item in result.history],
        pagination=result.pagination,
    )
    return context_success_response(data.model_dump(mode="json"), context)
