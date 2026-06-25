"""Scope search logs to authenticated users.

Revision ID: 20260625_0002
Revises: 20260624_0001
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260625_0002"
down_revision = "20260624_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("search_logs", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("search_logs", sa.Column("request_id", sa.Text(), nullable=True))

    op.execute("UPDATE search_logs SET request_id = 'legacy-migration' WHERE request_id IS NULL")
    op.execute("DELETE FROM search_logs WHERE user_id IS NULL")

    op.alter_column("search_logs", "user_id", nullable=False)
    op.alter_column("search_logs", "request_id", nullable=False)

    op.create_foreign_key(
        "fk_search_logs_user_id_users",
        "search_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_search_logs_user_id", "search_logs", ["user_id"])
    op.create_index("ix_search_logs_request_id", "search_logs", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_search_logs_request_id", table_name="search_logs")
    op.drop_index("ix_search_logs_user_id", table_name="search_logs")
    op.drop_constraint("fk_search_logs_user_id_users", "search_logs", type_="foreignkey")
    op.drop_column("search_logs", "request_id")
    op.drop_column("search_logs", "user_id")
