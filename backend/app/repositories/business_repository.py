from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Business
from app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Business)

