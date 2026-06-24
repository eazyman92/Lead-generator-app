from uuid import UUID, uuid4

from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class Business(TimestampMixin, Base):
    __tablename__ = "businesses"
    __table_args__ = (
        Index("ix_businesses_country_state_city", "country", "state", "city"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    industry: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    website: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)

    contacts = relationship("Contact", back_populates="business")
    data_sources = relationship("DataSource", back_populates="business")
    social_profiles = relationship("SocialProfile", back_populates="business")

