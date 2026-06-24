from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SocialProfile(Base):
    __tablename__ = "social_profiles"
    __table_args__ = (
        CheckConstraint(
            "platform IN ('facebook', 'instagram', 'linkedin', 'youtube')",
            name="platform_allowed",
        ),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    business = relationship("Business", back_populates="social_profiles")

