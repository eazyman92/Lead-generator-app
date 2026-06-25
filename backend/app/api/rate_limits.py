from typing import Protocol

from app.core.dependencies import RequestContext
from app.core.exceptions import RateLimitError
from app.core.rate_limit import check_search_rate_limit
from app.models import User


class RateLimitAuditService(Protocol):
    async def audit_rate_limit_denied(
        self,
        user: User,
        context: RequestContext,
        scope: str,
    ) -> None:
        ...


async def enforce_search_domain_rate_limit(
    user: User,
    context: RequestContext,
    service: RateLimitAuditService,
    scope: str,
) -> None:
    """Apply V1 search-domain rate limiting and audit denials."""
    try:
        check_search_rate_limit(user.id, scope)
    except RateLimitError:
        await service.audit_rate_limit_denied(user, context, scope)
        raise
