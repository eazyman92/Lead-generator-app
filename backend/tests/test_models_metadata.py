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


def test_required_indexes_are_present() -> None:
    indexes_by_table = {
        table_name: {index.name for index in table.indexes}
        for table_name, table in Base.metadata.tables.items()
    }

    assert "ix_businesses_country_state_city" in indexes_by_table["businesses"]
    assert "ix_businesses_industry" in indexes_by_table["businesses"]
    assert "ix_businesses_name" in indexes_by_table["businesses"]
    assert "ix_contacts_business_id" in indexes_by_table["contacts"]
    assert "ix_contacts_role" in indexes_by_table["contacts"]
    assert "ix_contacts_is_decision_maker" in indexes_by_table["contacts"]
    assert "ix_refresh_tokens_user_id" in indexes_by_table["refresh_tokens"]
    assert "ix_refresh_tokens_token_hash" in indexes_by_table["refresh_tokens"]
    assert "ix_background_jobs_status" in indexes_by_table["background_jobs"]
    assert "ix_background_jobs_job_type" in indexes_by_table["background_jobs"]
    assert "ix_background_jobs_locked_at" in indexes_by_table["background_jobs"]
    assert "ix_exports_user_id" in indexes_by_table["exports"]
    assert "ix_exports_status" in indexes_by_table["exports"]

