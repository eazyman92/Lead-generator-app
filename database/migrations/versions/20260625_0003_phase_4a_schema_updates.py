"""Add Phase 4A contact traceability and idempotency constraints.

Revision ID: 20260625_0003
Revises: 20260625_0002
Create Date: 2026-06-25
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260625_0003"
down_revision = "20260625_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "contacts",
        sa.Column("collection_timestamp", sa.DateTime(timezone=True), nullable=True),
    )

    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            UPDATE contacts
            SET collection_timestamp = created_at
            WHERE collection_timestamp IS NULL
            """
        )
    )

    # Resolve pre-existing duplicate source rows before adding the unique
    # constraint. The canonical row is the most trusted source, then highest
    # confidence, then earliest collection timestamp, then lowest UUID text.
    connection.execute(
        sa.text(
            """
            WITH ranked_sources AS (
                SELECT
                    id,
                    row_number() OVER (
                        PARTITION BY business_id, source_url
                        ORDER BY
                            CASE trust_tier
                                WHEN 'A' THEN 1
                                WHEN 'B' THEN 2
                                WHEN 'C' THEN 3
                                WHEN 'D' THEN 4
                                ELSE 5
                            END ASC,
                            confidence_score DESC NULLS LAST,
                            collected_at ASC NULLS LAST,
                            id::text ASC
                    ) AS source_rank
                FROM data_sources
                WHERE source_url IS NOT NULL
            )
            DELETE FROM data_sources ds
            USING ranked_sources ranked
            WHERE ds.id = ranked.id
              AND ranked.source_rank > 1
            """
        )
    )

    missing_sources = connection.execute(
        sa.text(
            """
            SELECT DISTINCT c.business_id, c.source_url, min(c.created_at) AS collected_at
            FROM contacts c
            WHERE c.source_url IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM data_sources ds
                  WHERE ds.business_id = c.business_id
                    AND ds.source_url = c.source_url
              )
            GROUP BY c.business_id, c.source_url
            """
        )
    )

    for source in missing_sources:
        connection.execute(
            sa.text(
                """
                INSERT INTO data_sources (
                    id,
                    business_id,
                    source_type,
                    source_url,
                    trust_tier,
                    confidence_score,
                    collected_at
                )
                VALUES (
                    :id,
                    :business_id,
                    'website',
                    :source_url,
                    'C',
                    50,
                    :collected_at
                )
                """
            ),
            {
                "id": uuid4(),
                "business_id": source.business_id,
                "source_url": source.source_url,
                "collected_at": source.collected_at,
            },
        )

    connection.execute(
        sa.text(
            """
            UPDATE contacts c
            SET source_id = ds.id
            FROM data_sources ds
            WHERE c.source_id IS NULL
              AND ds.business_id = c.business_id
              AND ds.source_url = c.source_url
            """
        )
    )

    unmapped_contacts = connection.scalar(
        sa.text(
            """
            SELECT count(*)
            FROM contacts
            WHERE source_id IS NULL
            """
        )
    )
    if unmapped_contacts:
        raise RuntimeError(
            "Phase 4A migration could not map all contacts to data_sources before "
            "enforcing contacts.source_id."
        )

    op.alter_column("contacts", "source_id", nullable=False)
    op.alter_column("contacts", "collection_timestamp", nullable=False)

    op.create_foreign_key(
        "fk_contacts_source_id_data_sources",
        "contacts",
        "data_sources",
        ["source_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_contacts_source_id", "contacts", ["source_id"])
    op.create_index("ix_contacts_collection_timestamp", "contacts", ["collection_timestamp"])

    op.create_unique_constraint(
        "uq_data_sources_business_source_url",
        "data_sources",
        ["business_id", "source_url"],
    )

    # Resolve pre-existing duplicate contacts before adding retry-safety
    # indexes. Contact identity follows the documented fallback order:
    # email, then phone, then name/source URL. The oldest collected row wins,
    # with created_at and UUID text as deterministic tie-breakers.
    connection.execute(
        sa.text(
            """
            WITH ranked_email_contacts AS (
                SELECT
                    id,
                    row_number() OVER (
                        PARTITION BY business_id, source_id, lower(email)
                        ORDER BY collection_timestamp ASC, created_at ASC, id::text ASC
                    ) AS contact_rank
                FROM contacts
                WHERE email IS NOT NULL
            )
            DELETE FROM contacts c
            USING ranked_email_contacts ranked
            WHERE c.id = ranked.id
              AND ranked.contact_rank > 1
            """
        )
    )
    connection.execute(
        sa.text(
            """
            WITH ranked_phone_contacts AS (
                SELECT
                    id,
                    row_number() OVER (
                        PARTITION BY business_id, source_id, phone
                        ORDER BY collection_timestamp ASC, created_at ASC, id::text ASC
                    ) AS contact_rank
                FROM contacts
                WHERE email IS NULL
                  AND phone IS NOT NULL
            )
            DELETE FROM contacts c
            USING ranked_phone_contacts ranked
            WHERE c.id = ranked.id
              AND ranked.contact_rank > 1
            """
        )
    )
    connection.execute(
        sa.text(
            """
            WITH ranked_name_contacts AS (
                SELECT
                    id,
                    row_number() OVER (
                        PARTITION BY business_id, source_id, lower(full_name), source_url
                        ORDER BY collection_timestamp ASC, created_at ASC, id::text ASC
                    ) AS contact_rank
                FROM contacts
                WHERE email IS NULL
                  AND phone IS NULL
            )
            DELETE FROM contacts c
            USING ranked_name_contacts ranked
            WHERE c.id = ranked.id
              AND ranked.contact_rank > 1
            """
        )
    )

    op.create_index(
        "ux_contacts_business_source_email",
        "contacts",
        ["business_id", "source_id", sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )
    op.create_index(
        "ux_contacts_business_source_phone",
        "contacts",
        ["business_id", "source_id", "phone"],
        unique=True,
        postgresql_where=sa.text("email IS NULL AND phone IS NOT NULL"),
    )
    op.create_index(
        "ux_contacts_business_source_name_url",
        "contacts",
        ["business_id", "source_id", sa.text("lower(full_name)"), "source_url"],
        unique=True,
        postgresql_where=sa.text("email IS NULL AND phone IS NULL"),
    )
    op.create_index(
        "ux_background_jobs_active_idempotency",
        "background_jobs",
        ["job_type", sa.text("(payload->>'idempotency_key')")],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("ux_background_jobs_active_idempotency", table_name="background_jobs")
    op.drop_index("ux_contacts_business_source_name_url", table_name="contacts")
    op.drop_index("ux_contacts_business_source_phone", table_name="contacts")
    op.drop_index("ux_contacts_business_source_email", table_name="contacts")
    op.drop_constraint("uq_data_sources_business_source_url", "data_sources", type_="unique")
    op.drop_index("ix_contacts_collection_timestamp", table_name="contacts")
    op.drop_index("ix_contacts_source_id", table_name="contacts")
    op.drop_constraint("fk_contacts_source_id_data_sources", "contacts", type_="foreignkey")
    op.drop_column("contacts", "collection_timestamp")
    op.drop_column("contacts", "source_id")
