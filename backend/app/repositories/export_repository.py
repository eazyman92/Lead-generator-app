from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Export
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[Export]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Export)

