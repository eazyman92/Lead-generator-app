from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DataSource
from app.repositories.base import BaseRepository


class DataSourceRepository(BaseRepository[DataSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DataSource)

    async def list_by_business_id(
        self,
        business_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataSource]:
        """Return data sources for a business."""
        statement = (
            select(DataSource)
            .where(DataSource.business_id == business_id)
            .order_by(DataSource.collected_at.desc(), DataSource.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def count_by_business_id(self, business_id: UUID) -> int:
        """Return source count for a business."""
        statement = select(func.count()).select_from(DataSource).where(
            DataSource.business_id == business_id
        )
        return int(await self.session.scalar(statement) or 0)

    async def get_by_business_and_url(
        self,
        business_id: UUID,
        source_url: str,
    ) -> DataSource | None:
        """Return a data source by the Phase 4A unique source identity."""
        statement = select(DataSource).where(
            DataSource.business_id == business_id,
            DataSource.source_url == source_url,
        )
        return await self.session.scalar(statement)
