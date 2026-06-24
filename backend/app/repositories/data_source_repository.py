from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DataSource
from app.repositories.base import BaseRepository


class DataSourceRepository(BaseRepository[DataSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DataSource)

