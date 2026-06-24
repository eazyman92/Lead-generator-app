from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLog)

    async def log_event(
        self,
        event_type: str,
        request_id: str,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Persist a security audit event."""
        return await self.create(
            {
                "event_type": event_type,
                "request_id": request_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "event_metadata": metadata or {},
            }
        )
