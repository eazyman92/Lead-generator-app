from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from collectors.models import RawBusiness, RawContact, RawSocialProfile
from collectors.normalization import deterministic_business_identity

SUPPORTED_SOCIAL_PLATFORMS = {"facebook", "instagram", "linkedin", "youtube", "x", "website"}


class CollectorRepository:
    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def close(self) -> None:
        await self.engine.dispose()

    async def load_job_payload(self, session: AsyncSession, job_id: str) -> dict[str, Any]:
        statement = text("SELECT payload FROM background_jobs WHERE id = :job_id")
        payload = await session.scalar(statement, {"job_id": UUID(job_id)})
        return dict(payload or {})

    async def update_progress(
        self,
        session: AsyncSession,
        job_id: str,
        progress: dict[str, Any],
    ) -> None:
        payload = await self.load_job_payload(session, job_id)
        payload["progress"] = progress
        statement = (
            text(
                """
                UPDATE background_jobs
                SET payload = :payload,
                    updated_at = now()
                WHERE id = :job_id
                """
            )
            .bindparams(bindparam("payload", type_=JSONB))
        )
        await session.execute(statement, {"job_id": UUID(job_id), "payload": payload})

    async def audit(
        self,
        session: AsyncSession,
        event_type: str,
        request_id: str,
        user_id: str | None,
        metadata: dict[str, Any],
    ) -> None:
        statement = (
            text(
                """
                INSERT INTO audit_logs (
                    id, user_id, event_type, ip_address, request_id, metadata, created_at
                )
                VALUES (
                    :id, :user_id, :event_type, NULL, :request_id, :metadata, now()
                )
                """
            )
            .bindparams(bindparam("metadata", type_=JSONB))
        )
        await session.execute(
            statement,
            {
                "id": uuid4(),
                "user_id": UUID(user_id) if user_id else None,
                "event_type": event_type,
                "request_id": request_id,
                "metadata": metadata,
            },
        )

    async def save_business(
        self,
        session: AsyncSession,
        business: RawBusiness,
    ) -> tuple[UUID, bool]:
        existing_id = await self.find_business(session, business)
        if existing_id is not None:
            await session.execute(
                text(
                    """
                    UPDATE businesses
                    SET name = :name,
                        industry = :industry,
                        website = :website,
                        phone = :phone,
                        email = :email,
                        country = :country,
                        state = :state,
                        city = :city,
                        address = :address,
                        description = :description,
                        source_type = :source_type,
                        updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"id": existing_id, **self._business_values(business)},
            )
            return existing_id, False

        business_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO businesses (
                    id, name, industry, website, phone, email, country, state, city,
                    address, description, source_type, created_at, updated_at
                )
                VALUES (
                    :id, :name, :industry, :website, :phone, :email, :country, :state,
                    :city, :address, :description, :source_type, now(), now()
                )
                """
            ),
            {"id": business_id, **self._business_values(business)},
        )
        return business_id, True

    async def find_business(self, session: AsyncSession, business: RawBusiness) -> UUID | None:
        identity = deterministic_business_identity(business)
        if identity.startswith("website:") and business.website:
            return await session.scalar(
                text("SELECT id FROM businesses WHERE lower(website) = lower(:website) LIMIT 1"),
                {"website": business.website},
            )
        if identity.startswith("phone:") and business.phone:
            return await session.scalar(
                text("SELECT id FROM businesses WHERE phone = :phone LIMIT 1"),
                {"phone": business.phone},
            )
        return await session.scalar(
            text(
                """
                SELECT id
                FROM businesses
                WHERE lower(name) = lower(:name)
                  AND lower(country) = lower(:country)
                  AND lower(state) = lower(:state)
                  AND lower(city) = lower(:city)
                LIMIT 1
                """
            ),
            {
                "name": business.name,
                "country": business.country,
                "state": business.state,
                "city": business.city,
            },
        )

    async def save_data_source(
        self,
        session: AsyncSession,
        business_id: UUID,
        business: RawBusiness,
    ) -> UUID:
        source_id = uuid4()
        statement = text(
            """
            INSERT INTO data_sources (
                id, business_id, source_type, source_url, trust_tier,
                confidence_score, collected_at
            )
            VALUES (
                :id, :business_id, :source_type, :source_url, :trust_tier,
                :confidence_score, :collected_at
            )
            ON CONFLICT ON CONSTRAINT uq_data_sources_business_source_url
            DO UPDATE SET
                source_type = EXCLUDED.source_type,
                trust_tier = EXCLUDED.trust_tier,
                confidence_score = EXCLUDED.confidence_score,
                collected_at = EXCLUDED.collected_at
            RETURNING id
            """
        )
        return await session.scalar(
            statement,
            {
                "id": source_id,
                "business_id": business_id,
                "source_type": business.source_type,
                "source_url": business.source_url or business.website or "manual",
                "trust_tier": business.trust_tier,
                "confidence_score": business.confidence_score,
                "collected_at": datetime.now(timezone.utc),
            },
        )

    async def save_contact(
        self,
        session: AsyncSession,
        business_id: UUID,
        source_id: UUID,
        contact: RawContact,
    ) -> tuple[UUID, bool]:
        existing_id = await self.find_contact(session, business_id, source_id, contact)
        values = {
            "business_id": business_id,
            "source_id": source_id,
            "full_name": contact.full_name,
            "role": contact.role,
            "email": contact.email,
            "phone": contact.phone,
            "linkedin_url": contact.linkedin_url,
            "source_url": contact.source_url,
            "collection_timestamp": datetime.now(timezone.utc),
        }
        if existing_id is not None:
            await session.execute(
                text(
                    """
                    UPDATE contacts
                    SET full_name = :full_name,
                        role = :role,
                        email = :email,
                        phone = :phone,
                        linkedin_url = :linkedin_url,
                        source_url = :source_url,
                        collection_timestamp = :collection_timestamp
                    WHERE id = :id
                    """
                ),
                {"id": existing_id, **values},
            )
            return existing_id, False

        contact_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO contacts (
                    id, business_id, source_id, full_name, role, email, phone,
                    linkedin_url, is_decision_maker, priority_score, source_url,
                    collection_timestamp, created_at
                )
                VALUES (
                    :id, :business_id, :source_id, :full_name, :role, :email, :phone,
                    :linkedin_url, false, 0, :source_url, :collection_timestamp, now()
                )
                """
            ),
            {"id": contact_id, **values},
        )
        return contact_id, True

    async def find_contact(
        self,
        session: AsyncSession,
        business_id: UUID,
        source_id: UUID,
        contact: RawContact,
    ) -> UUID | None:
        if contact.email:
            return await session.scalar(
                text(
                    """
                    SELECT id FROM contacts
                    WHERE business_id = :business_id
                      AND source_id = :source_id
                      AND lower(email) = lower(:email)
                    LIMIT 1
                    """
                ),
                {"business_id": business_id, "source_id": source_id, "email": contact.email},
            )
        if contact.phone:
            return await session.scalar(
                text(
                    """
                    SELECT id FROM contacts
                    WHERE business_id = :business_id
                      AND source_id = :source_id
                      AND email IS NULL
                      AND phone = :phone
                    LIMIT 1
                    """
                ),
                {"business_id": business_id, "source_id": source_id, "phone": contact.phone},
            )
        return await session.scalar(
            text(
                """
                SELECT id FROM contacts
                WHERE business_id = :business_id
                  AND source_id = :source_id
                  AND email IS NULL
                  AND phone IS NULL
                  AND lower(full_name) = lower(:full_name)
                  AND source_url = :source_url
                LIMIT 1
                """
            ),
            {
                "business_id": business_id,
                "source_id": source_id,
                "full_name": contact.full_name,
                "source_url": contact.source_url,
            },
        )

    async def save_social_profile(
        self,
        session: AsyncSession,
        business_id: UUID,
        profile: RawSocialProfile,
    ) -> tuple[UUID | None, bool]:
        if profile.platform not in SUPPORTED_SOCIAL_PLATFORMS:
            return None, False
        existing_id = await session.scalar(
            text(
                """
                SELECT id FROM social_profiles
                WHERE business_id = :business_id
                  AND platform = :platform
                  AND url = :url
                LIMIT 1
                """
            ),
            {"business_id": business_id, "platform": profile.platform, "url": profile.url},
        )
        if existing_id is not None:
            return existing_id, False
        social_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO social_profiles (id, business_id, platform, url)
                VALUES (:id, :business_id, :platform, :url)
                """
            ),
            {
                "id": social_id,
                "business_id": business_id,
                "platform": profile.platform,
                "url": profile.url,
            },
        )
        return social_id, True

    def _business_values(self, business: RawBusiness) -> dict[str, Any]:
        return {
            "name": business.name,
            "industry": business.industry,
            "website": business.website,
            "phone": business.phone,
            "email": business.email,
            "country": business.country,
            "state": business.state,
            "city": business.city,
            "address": business.address,
            "description": business.description,
            "source_type": business.source_type,
        }
