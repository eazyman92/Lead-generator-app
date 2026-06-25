# Phase 4 Gap Remediation Report

Date: 2026-06-25

Project: Lead Generator App

Scope: Documentation-only remediation of Critical Blockers and Major Issues from `docs/phase-4-final-independent-validation.md`.

No application code, migrations, Docker Compose files, or environment template files were modified.

## Critical Blockers Resolved

### 1. Contact source traceability schema gap

Resolution:

* Updated `docs/database-erd.md` from Phase 3 schema scope to Phase 4A target schema scope.
* Added `contacts.source_id`.
* Added `contacts.collection_timestamp`.
* Added `fk_contacts_source_id_data_sources`.
* Added indexes for `contacts.source_id` and `contacts.collection_timestamp`.
* Added the required contact partial unique indexes.
* Added `data_sources ||--o{ contacts` to the ERD.

Updated files:

* `docs/database-erd.md`
* `docs/data-model.md`

### 2. Schema-change policy conflict

Resolution:

* Clarified that queue metadata remains in `background_jobs.payload`.
* Clarified that Phase 4A may add required database indexes and constraints for source traceability, deduplication, and idempotency.
* Added Phase 4A database migration scope to the roadmap.

Updated files:

* `docs/job-queue-design.md`
* `docs/data-model.md`
* `docs/database-erd.md`
* `docs/implementation-roadmap.md`

## Major Issues Resolved

### 1. Race-safe idempotency enforcement

Resolution:

Defined the canonical PostgreSQL partial unique index:

```text
ux_background_jobs_active_idempotency
ON background_jobs (job_type, (payload->>'idempotency_key'))
WHERE status IN ('pending', 'running')
```

Updated files:

* `docs/job-queue-design.md`
* `docs/background-job-spec.md`
* `docs/internal-api-contracts.md`
* `docs/api-spec.md`
* `docs/database-erd.md`
* `docs/data-model.md`

### 2. Contact and data-source deduplication constraints

Resolution:

Defined:

* `uq_data_sources_business_source_url`
* `ux_contacts_business_source_email`
* `ux_contacts_business_source_phone`
* `ux_contacts_business_source_name_url`

Updated files:

* `docs/data-model.md`
* `docs/database-erd.md`
* `docs/contact-collection-design.md`

### 3. Audit event name drift

Resolution:

Established:

* `background_job_*` events for job lifecycle state changes
* `contact_collection_*` events for contact-domain activity

Removed `contact_collection_job_*` from active Phase 4 docs.

Updated files:

* `docs/job-queue-design.md`
* `docs/contact-collection-design.md`
* `docs/data-acquisition-strategy-v1.md`

### 4. Internal job status response mismatch

Resolution:

Updated `GET /internal/v1/jobs/{job_id}` response to include:

* `retry_after`
* `dead_letter_reason`
* `cancelled`
* `cancelled_reason`
* `last_error_code`
* `last_error_at`

Updated files:

* `docs/internal-api-contracts.md`

### 5. Job error taxonomy drift

Resolution:

Canonicalized job errors across active Phase 4 docs:

* `INVALID_PAYLOAD`
* `SOURCE_AUTH_REQUIRED`
* `SOURCE_FORBIDDEN`
* `BUSINESS_NOT_FOUND`
* shared retry and terminal job error names

Removed active use of conflicting `INVALID_JOB_PAYLOAD`, `HTTP_401`, and `HTTP_403` job error names.

Updated files:

* `docs/api-spec.md`
* `docs/background-job-spec.md`
* `docs/internal-api-contracts.md`
* `docs/job-queue-design.md`
* `docs/contact-collection-design.md`

### 6. Worker environment variable documentation

Resolution:

Updated deployment documentation to list all Phase 4 worker environment variables and state that Phase 4A implementation must add them to `.env.example` and pass them through the `worker` service in `docker-compose.yml`.

Updated files:

* `docs/deployment-guide.md`

### 7. Contact field encryption ownership

Resolution:

Defined repository-boundary ownership for contact email and phone encryption using `ENCRYPTION_KEY`.

Rules now state:

* services normalize contact values
* repositories encrypt before insert/update
* repositories decrypt only for authorized responses
* raw contact values must not be stored in logs, job payloads, audit metadata, or errors
* traceability fields remain queryable

Updated files:

* `docs/api-spec.md`
* `docs/contact-collection-design.md`
* `docs/data-model.md`
* `docs/security-standards.md`

## Additional Minor Cleanup

Updated `docs/compliance-policy.md` so contact traceability is described through `contacts.source_id -> data_sources.id` instead of implying all source metadata must be duplicated on each contact record.

## Remaining Unresolved Critical Blockers

None.

## Remaining Unresolved Major Issues

None.

## Notes

Because this pass was documentation-only, required migrations and infrastructure wiring remain implementation tasks for Phase 4A rather than completed repository changes.
