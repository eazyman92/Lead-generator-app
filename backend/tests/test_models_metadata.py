from sqlalchemy import UniqueConstraint
from sqlalchemy import CheckConstraint

from app.models import Base


def test_core_v1_tables_are_registered() -> None:
    expected_tables = {
        "audit_logs",
        "background_jobs",
        "businesses",
        "contacts",
        "data_sources",
        "exports",
        "refresh_tokens",
        "search_logs",
        "social_profiles",
        "users",
    }

    assert set(Base.metadata.tables) == expected_tables


def test_future_tables_are_not_registered_for_phase_1() -> None:
    assert "business_enrichment" not in Base.metadata.tables
    assert "opportunity_scores" not in Base.metadata.tables


def test_refresh_tokens_table_matches_lifecycle_spec() -> None:
    table = Base.metadata.tables["refresh_tokens"]

    expected_columns = {
        "id",
        "user_id",
        "token_hash",
        "issued_at",
        "expires_at",
        "revoked_at",
        "replaced_by_token_id",
        "created_ip",
        "user_agent",
        "last_used_at",
    }

    assert set(table.columns.keys()) == expected_columns
    assert table.c.token_hash.unique is True


def test_search_logs_uses_canonical_table_name() -> None:
    assert "search_logs" in Base.metadata.tables
    assert "search_queries" not in Base.metadata.tables


def test_search_logs_are_user_scoped() -> None:
    table = Base.metadata.tables["search_logs"]

    assert "user_id" in table.columns
    assert "request_id" in table.columns
    assert table.c.user_id.nullable is False
    assert table.c.request_id.nullable is False


def test_required_indexes_are_present() -> None:
    indexes_by_table = {
        table_name: {index.name for index in table.indexes}
        for table_name, table in Base.metadata.tables.items()
    }

    assert "ix_businesses_country_state_city" in indexes_by_table["businesses"]
    assert "ix_businesses_industry" in indexes_by_table["businesses"]
    assert "ix_businesses_name" in indexes_by_table["businesses"]
    assert "ix_contacts_business_id" in indexes_by_table["contacts"]
    assert "ix_contacts_source_id" in indexes_by_table["contacts"]
    assert "ix_contacts_collection_timestamp" in indexes_by_table["contacts"]
    assert "ix_contacts_role" in indexes_by_table["contacts"]
    assert "ix_contacts_is_decision_maker" in indexes_by_table["contacts"]
    assert "ux_contacts_business_source_email" in indexes_by_table["contacts"]
    assert "ux_contacts_business_source_phone" in indexes_by_table["contacts"]
    assert "ux_contacts_business_source_name_url" in indexes_by_table["contacts"]
    assert "ix_refresh_tokens_user_id" in indexes_by_table["refresh_tokens"]
    assert "ix_refresh_tokens_token_hash" in indexes_by_table["refresh_tokens"]
    assert "ix_background_jobs_status" in indexes_by_table["background_jobs"]
    assert "ix_background_jobs_job_type" in indexes_by_table["background_jobs"]
    assert "ix_background_jobs_locked_at" in indexes_by_table["background_jobs"]
    assert "ux_background_jobs_active_idempotency" in indexes_by_table["background_jobs"]
    assert "ix_exports_user_id" in indexes_by_table["exports"]
    assert "ix_exports_status" in indexes_by_table["exports"]
    assert "ix_search_logs_user_id" in indexes_by_table["search_logs"]
    assert "ix_search_logs_request_id" in indexes_by_table["search_logs"]


def test_phase_4a_contact_traceability_metadata_is_registered() -> None:
    contacts = Base.metadata.tables["contacts"]

    assert "source_id" in contacts.columns
    assert "collection_timestamp" in contacts.columns
    assert contacts.c.source_id.nullable is False
    assert contacts.c.collection_timestamp.nullable is False

    foreign_keys = {
        fk.constraint.name
        for fk in contacts.foreign_keys
    }
    assert "fk_contacts_source_id_data_sources" in foreign_keys


def test_phase_4a_uniqueness_constraints_are_registered() -> None:
    data_sources = Base.metadata.tables["data_sources"]

    unique_constraints = {
        constraint.name
        for constraint in data_sources.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_data_sources_business_source_url" in unique_constraints


def test_phase_4b_social_profile_platform_metadata_is_registered() -> None:
    social_profiles = Base.metadata.tables["social_profiles"]

    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in social_profiles.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_social_profiles_platform_allowed" in checks
    assert "'x'" in checks["ck_social_profiles_platform_allowed"]
    assert "'website'" in checks["ck_social_profiles_platform_allowed"]
