from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SocialProfile
from app.repositories.base import BaseRepository


class SocialProfileRepository(BaseRepository[SocialProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SocialProfile)

    async def list_by_business_id(
        self,
        business_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SocialProfile]:
        """Return social profiles for a business."""
        statement = (
            select(SocialProfile)
            .where(SocialProfile.business_id == business_id)
            .order_by(SocialProfile.platform.asc(), SocialProfile.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def count_by_business_id(self, business_id: UUID) -> int:
        """Return social profile count for a business."""
        statement = select(func.count()).select_from(SocialProfile).where(
            SocialProfile.business_id == business_id
        )
        return int(await self.session.scalar(statement) or 0)
