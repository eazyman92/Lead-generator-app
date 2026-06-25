from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import CreatedAtMixin


class Contact(CreatedAtMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_decision_maker: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    collection_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    business = relationship("Business", back_populates="contacts")
    source = relationship("DataSource", back_populates="contacts")

    __table_args__ = (
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 100",
            name="priority_score_range",
        ),
    )


Index(
    "ux_contacts_business_source_email",
    Contact.business_id,
    Contact.source_id,
    func.lower(Contact.email),
    unique=True,
    postgresql_where=Contact.email.is_not(None),
)
Index(
    "ux_contacts_business_source_phone",
    Contact.business_id,
    Contact.source_id,
    Contact.phone,
    unique=True,
    postgresql_where=Contact.email.is_(None) & Contact.phone.is_not(None),
)
Index(
    "ux_contacts_business_source_name_url",
    Contact.business_id,
    Contact.source_id,
    func.lower(Contact.full_name),
    Contact.source_url,
    unique=True,
    postgresql_where=Contact.email.is_(None) & Contact.phone.is_(None),
)
