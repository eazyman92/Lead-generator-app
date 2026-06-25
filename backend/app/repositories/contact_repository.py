from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Contact)

    async def list_by_business_id(
        self,
        business_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Contact]:
        """Return contacts for a business."""
        statement = (
            select(Contact)
            .where(Contact.business_id == business_id)
            .order_by(Contact.created_at.desc(), Contact.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def count_by_business_id(self, business_id: UUID) -> int:
        """Return contact count for a business."""
        statement = select(func.count()).select_from(Contact).where(Contact.business_id == business_id)
        return int(await self.session.scalar(statement) or 0)

    async def list_by_source_id(
        self,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Contact]:
        """Return contacts traced to one data source."""
        statement = (
            select(Contact)
            .where(Contact.source_id == source_id)
            .order_by(Contact.collection_timestamp.desc(), Contact.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all())
