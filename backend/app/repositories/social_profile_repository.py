from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SocialProfile
from app.repositories.base import BaseRepository


class SocialProfileRepository(BaseRepository[SocialProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SocialProfile)

