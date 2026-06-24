from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized email address."""
        statement = select(User).where(User.email == email)
        return await self.session.scalar(statement)

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by id."""
        return await self.get(user_id)
