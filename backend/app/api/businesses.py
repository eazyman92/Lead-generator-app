from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rate_limits import enforce_search_domain_rate_limit
from app.api.responses import context_success_response
from app.core.dependencies import RequestContext, get_request_context, require_permissions
from app.models import User
from app.repositories.database import get_session
from app.schemas.business_detail import (
    BusinessContactsData,
    BusinessDetailBusiness,
    BusinessDetailContact,
    BusinessDetailData,
    BusinessDetailSource,
    BusinessSourcesData,
)
from app.schemas.search import PaginationRequest
from app.services.business_service import BusinessService

router = APIRouter(prefix="/api/v1/businesses", tags=["businesses"])


def get_business_service(session: AsyncSession = Depends(get_session)) -> BusinessService:
    """Provide the business service."""
    return BusinessService(session)


@router.get("/{business_id}")
async def get_business(
    business_id: UUID,
    user: User = Depends(require_permissions("business:read")),
    context: RequestContext = Depends(get_request_context),
    service: BusinessService = Depends(get_business_service),
) -> dict[str, object]:
    """Return one business with V1 related summary counts."""
    await enforce_search_domain_rate_limit(user, context, service, "business_detail")
    result = await service.get_detail(business_id, user, context)
    business = BusinessDetailBusiness.model_validate(result.business).model_copy(
        update={
            "contacts_count": result.contacts_count,
            "sources_count": result.sources_count,
            "social_profiles_count": result.social_profiles_count,
        }
    )
    data = BusinessDetailData(
        business=business,
    )
    return context_success_response(data.model_dump(mode="json"), context)


@router.get("/{business_id}/contacts")
async def get_business_contacts(
    business_id: UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permissions("contact:read")),
    context: RequestContext = Depends(get_request_context),
    service: BusinessService = Depends(get_business_service),
) -> dict[str, object]:
    """Return paginated public contacts for one business."""
    await enforce_search_domain_rate_limit(user, context, service, "business_contacts")
    pagination = PaginationRequest(page=page, per_page=per_page)
    result = await service.get_contacts(business_id, pagination, user, context)
    data = BusinessContactsData(
        business_id=result.business_id,
        contacts=[BusinessDetailContact.model_validate(contact) for contact in result.contacts],
        pagination=result.pagination,
    )
    return context_success_response(data.model_dump(mode="json"), context)


@router.get("/{business_id}/sources")
async def get_business_sources(
    business_id: UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user: User = Depends(require_permissions("source:read")),
    context: RequestContext = Depends(get_request_context),
    service: BusinessService = Depends(get_business_service),
) -> dict[str, object]:
    """Return paginated source attribution for one business."""
    await enforce_search_domain_rate_limit(user, context, service, "business_sources")
    pagination = PaginationRequest(page=page, per_page=per_page)
    result = await service.get_sources(business_id, pagination, user, context)
    data = BusinessSourcesData(
        business_id=result.business_id,
        sources=[
            BusinessDetailSource.model_validate(source) for source in result.data_sources
        ],
        pagination=result.pagination,
    )
    return context_success_response(data.model_dump(mode="json"), context)
