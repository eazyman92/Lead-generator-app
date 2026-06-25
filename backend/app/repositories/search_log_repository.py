from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SearchLog
from app.repositories.base import BaseRepository


class SearchLogRepository(BaseRepository[SearchLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SearchLog)

    async def list_history(self, user_id: UUID, limit: int, offset: int) -> list[SearchLog]:
        """Return user-scoped search history ordered by newest first."""
        statement = (
            select(SearchLog)
            .where(SearchLog.user_id == user_id)
            .order_by(SearchLog.created_at.desc(), SearchLog.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def count_history(self, user_id: UUID) -> int:
        """Return total user-scoped search history rows."""
        statement = select(func.count()).select_from(SearchLog).where(SearchLog.user_id == user_id)
        return int(await self.session.scalar(statement) or 0)
