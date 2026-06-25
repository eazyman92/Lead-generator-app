from pathlib import Path


def test_initial_migration_contains_core_tables() -> None:
    migration = Path("database/migrations/versions/20260624_0001_initial_core_schema.py")
    content = migration.read_text(encoding="utf-8")

    for table_name in [
        "users",
        "refresh_tokens",
        "businesses",
        "contacts",
        "data_sources",
        "social_profiles",
        "search_logs",
        "exports",
        "background_jobs",
        "audit_logs",
    ]:
        assert f'"{table_name}"' in content


def test_initial_migration_excludes_future_tables() -> None:
    migration = Path("database/migrations/versions/20260624_0001_initial_core_schema.py")
    content = migration.read_text(encoding="utf-8")

    assert '"business_enrichment"' not in content
    assert '"opportunity_scores"' not in content
    assert '"search_queries"' not in content


def test_search_log_scope_migration_adds_user_traceability() -> None:
    migration = Path("database/migrations/versions/20260625_0002_scope_search_logs_to_users.py")
    content = migration.read_text(encoding="utf-8")

    assert '"user_id"' in content
    assert '"request_id"' in content
    assert "fk_search_logs_user_id_users" in content
    assert "ix_search_logs_user_id" in content
    assert "ix_search_logs_request_id" in content
