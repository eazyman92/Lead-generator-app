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


def test_phase_4a_migration_adds_contact_traceability_and_idempotency() -> None:
    migration = Path("database/migrations/versions/20260625_0003_phase_4a_schema_updates.py")
    content = migration.read_text(encoding="utf-8")

    for expected in [
        '"source_id"',
        '"collection_timestamp"',
        "fk_contacts_source_id_data_sources",
        "ix_contacts_source_id",
        "ix_contacts_collection_timestamp",
        "uq_data_sources_business_source_url",
        "ux_contacts_business_source_email",
        "ux_contacts_business_source_phone",
        "ux_contacts_business_source_name_url",
        "ux_background_jobs_active_idempotency",
    ]:
        assert expected in content


def test_phase_4a_migration_deduplicates_data_sources_deterministically() -> None:
    migration = Path("database/migrations/versions/20260625_0003_phase_4a_schema_updates.py")
    content = migration.read_text(encoding="utf-8")

    for expected in [
        "ranked_sources",
        "PARTITION BY business_id, source_url",
        "WHEN 'A' THEN 1",
        "WHEN 'B' THEN 2",
        "WHEN 'C' THEN 3",
        "WHEN 'D' THEN 4",
        "confidence_score DESC NULLS LAST",
        "collected_at ASC NULLS LAST",
        "id::text ASC",
        "ranked.source_rank > 1",
    ]:
        assert expected in content

    assert content.index("ranked_sources") < content.index("uq_data_sources_business_source_url")


def test_phase_4a_migration_deduplicates_contacts_before_unique_indexes() -> None:
    migration = Path("database/migrations/versions/20260625_0003_phase_4a_schema_updates.py")
    content = migration.read_text(encoding="utf-8")

    for expected in [
        "ranked_email_contacts",
        "PARTITION BY business_id, source_id, lower(email)",
        "ranked_phone_contacts",
        "PARTITION BY business_id, source_id, phone",
        "ranked_name_contacts",
        "PARTITION BY business_id, source_id, lower(full_name), source_url",
        "ORDER BY collection_timestamp ASC, created_at ASC, id::text ASC",
        "ranked.contact_rank > 1",
    ]:
        assert expected in content

    assert content.index("ranked_email_contacts") < content.index("ux_contacts_business_source_email")
    assert content.index("ranked_phone_contacts") < content.index("ux_contacts_business_source_phone")
    assert content.index("ranked_name_contacts") < content.index("ux_contacts_business_source_name_url")
