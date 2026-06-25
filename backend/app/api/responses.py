from typing import Any

from app.core.dependencies import RequestContext


def success_response(
    data: dict[str, Any],
    request_id: str,
    message: str | None = None,
) -> dict[str, Any]:
    """Return the standard API success response wrapper."""
    return {
        "success": True,
        "data": data,
        "message": message,
        "request_id": request_id,
    }


def context_success_response(
    data: dict[str, Any],
    context: RequestContext,
    message: str | None = None,
) -> dict[str, Any]:
    """Return the standard success wrapper using request context."""
    return success_response(data, context.request_id, message)
