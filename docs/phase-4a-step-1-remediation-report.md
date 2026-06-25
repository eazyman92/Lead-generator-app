# Phase 4A Step 1 Remediation Report

Project: Lead Generator App

Date: 2026-06-25

Scope: Phase 4A Step 1 remediation only. No worker jobs, contact collection services, queue processing, internal APIs, CSV export behavior, enrichment, scoring, or frontend changes were implemented.

## Remediation Summary

The Phase 4A schema migration was updated to handle pre-existing duplicate records deterministically before new uniqueness constraints are applied.

Resolved findings:

* Existing duplicate `contacts` rows are now removed before the contact partial unique indexes are created.
* Existing duplicate `data_sources` rows are now resolved with an explicit canonical-row policy before `uq_data_sources_business_source_url` is created.
* Migration behavior is documented in migration comments and in `docs/data-model.md`.
* Migration tests now verify that duplicate-resolution logic exists and runs before the relevant unique indexes and constraints are created.

## Deterministic Duplicate-Resolution Strategy

### Data Sources

Before applying `uq_data_sources_business_source_url`, duplicate `data_sources` rows for the same `(business_id, source_url)` are ranked.

The canonical row is selected by:

1. Highest trust tier: A, then B, then C, then D
2. Highest `confidence_score`
3. Earliest `collected_at`
4. Lowest `id` text value

Rows not selected as canonical duplicates are removed before the unique constraint is applied.

### Contacts

Before creating contact partial unique indexes, duplicate `contacts` rows are resolved using the documented identity fallback order:

1. `(business_id, source_id, lower(email))` when `email IS NOT NULL`
2. `(business_id, source_id, phone)` when `email IS NULL AND phone IS NOT NULL`
3. `(business_id, source_id, lower(full_name), source_url)` when `email IS NULL AND phone IS NULL`

For each duplicate group, the canonical row is selected by:

1. Earliest `collection_timestamp`
2. Earliest `created_at`
3. Lowest `id` text value

Rows not selected as canonical duplicates are removed before the partial unique indexes are created.

## Files Changed

* `database/migrations/versions/20260625_0003_phase_4a_schema_updates.py`
* `backend/tests/test_migration_definition.py`
* `docs/data-model.md`
* `docs/phase-4a-step-1-remediation-report.md`

## Tests Executed

```text
python -m py_compile database/migrations/versions/20260625_0003_phase_4a_schema_updates.py backend/tests/test_migration_definition.py
```

Result: passed

```text
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest backend/tests/test_migration_definition.py -q
```

Result: 6 passed

```text
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest backend/tests/test_migration_definition.py backend/tests/test_schemas.py -q
```

Result: 9 passed

## Validation Results

* Migration now deduplicates `data_sources` before applying `uq_data_sources_business_source_url`.
* Migration now deduplicates `contacts` before applying:
  * `ux_contacts_business_source_email`
  * `ux_contacts_business_source_phone`
  * `ux_contacts_business_source_name_url`
* Duplicate-resolution ordering is deterministic and documented.
* The migration fails explicitly if existing contacts cannot be mapped to a `data_sources` row before `contacts.source_id` is made non-nullable.
* No Phase 4A Step 2 repository, job lifecycle, worker, internal API, or service behavior was added.

## Blockers

No remediation blockers were discovered.

Live PostgreSQL migration execution was not performed in this pass; validation was limited to syntax checks and focused test coverage available in the local environment.
