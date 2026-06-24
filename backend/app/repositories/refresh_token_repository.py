from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RefreshToken)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Return a refresh token record by token hash."""
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return await self.session.scalar(statement)

    async def revoke(self, token: RefreshToken, revoked_at: datetime) -> RefreshToken:
        """Mark a refresh token as revoked."""
        token.revoked_at = revoked_at
        await self.session.flush()
        return token

    async def revoke_with_replacement(
        self,
        token: RefreshToken,
        revoked_at: datetime,
        replacement_id: UUID,
    ) -> RefreshToken:
        """Mark a refresh token as revoked and link its replacement."""
        token.revoked_at = revoked_at
        token.replaced_by_token_id = replacement_id
        token.last_used_at = revoked_at
        await self.session.flush()
        return token

    async def revoke_all_active_for_user(
        self,
        user_id: UUID,
        revoked_at: datetime,
    ) -> list[RefreshToken]:
        """Revoke all active refresh tokens for a user."""
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        result = await self.session.scalars(statement)
        tokens = list(result.all())
        for token in tokens:
            token.revoked_at = revoked_at
        await self.session.flush()
        return tokens
