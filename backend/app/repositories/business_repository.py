from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Business
from app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Business)

    async def search(
        self,
        industry: str,
        country: str,
        state: str,
        city: str,
        limit: int,
        offset: int,
    ) -> list[Business]:
        """Return businesses matching V1 search filters."""
        statement = (
            select(Business)
            .where(*self._search_conditions(industry, country, state, city))
            .order_by(Business.name.asc(), Business.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def count_search(
        self,
        industry: str,
        country: str,
        state: str,
        city: str,
    ) -> int:
        """Return total businesses matching V1 search filters."""
        statement = select(func.count()).select_from(Business).where(
            *self._search_conditions(industry, country, state, city)
        )
        return int(await self.session.scalar(statement) or 0)

    def _search_conditions(
        self,
        industry: str,
        country: str,
        state: str,
        city: str,
    ):
        return (
            func.lower(Business.industry) == industry.lower(),
            func.lower(Business.country) == country.lower(),
            func.lower(Business.state) == state.lower(),
            func.lower(Business.city) == city.lower(),
        )
