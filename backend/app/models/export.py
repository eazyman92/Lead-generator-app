from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class Export(TimestampMixin, Base):
    __tablename__ = "exports"
    __table_args__ = (
        CheckConstraint("format IN ('csv')", name="format_allowed"),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="status_allowed"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[str] = mapped_column(Text, nullable=False, default="csv")
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", index=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="exports")

