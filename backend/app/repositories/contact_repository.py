from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Contact)

