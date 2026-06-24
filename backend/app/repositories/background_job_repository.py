from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackgroundJob
from app.repositories.base import BaseRepository


class BackgroundJobRepository(BaseRepository[BackgroundJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BackgroundJob)

