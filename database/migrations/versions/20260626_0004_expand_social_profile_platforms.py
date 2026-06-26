"""Expand social profile platforms for Phase 4B collection.

Revision ID: 20260626_0004
Revises: 20260625_0003
Create Date: 2026-06-26
"""

from alembic import op

revision = "20260626_0004"
down_revision = "20260625_0003"
branch_labels = None
depends_on = None


NEW_PLATFORM_CHECK = "platform IN ('facebook', 'instagram', 'linkedin', 'youtube', 'x', 'website')"
OLD_PLATFORM_CHECK = "platform IN ('facebook', 'instagram', 'linkedin', 'youtube')"


def upgrade() -> None:
    op.drop_constraint(
        "ck_social_profiles_platform_allowed",
        "social_profiles",
        type_="check",
    )
    op.create_check_constraint(
        "ck_social_profiles_platform_allowed",
        "social_profiles",
        NEW_PLATFORM_CHECK,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_social_profiles_platform_allowed",
        "social_profiles",
        type_="check",
    )
    op.create_check_constraint(
        "ck_social_profiles_platform_allowed",
        "social_profiles",
        OLD_PLATFORM_CHECK,
    )
