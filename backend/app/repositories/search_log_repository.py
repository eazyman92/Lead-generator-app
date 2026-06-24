from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SearchLog
from app.repositories.base import BaseRepository


class SearchLogRepository(BaseRepository[SearchLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SearchLog)

