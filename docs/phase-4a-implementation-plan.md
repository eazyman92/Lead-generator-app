# Phase 4A Implementation Plan

Project: Lead Generator App

Scope: Planning only. Do not implement code from this document directly without a Phase 4A implementation task.

Phase 4A implements the MVP data acquisition foundation:

* PostgreSQL-backed background jobs
* internal worker APIs
* public contact collection from allowed sources
* retry and dead-letter handling
* audit logging
* CSV export job creation support

Phase 4A must not implement:

* decision-maker identification
* LinkedIn people discovery
* enrichment
* opportunity scoring
* AI intelligence workflows

## Step 1: Database Migration Updates

### Files Affected

* `database/migrations/versions/<new_phase_4a_migration>.py`
* `backend/app/models/contact.py`
* `backend/app/models/data_source.py`
* `backend/app/models/background_job.py`
* `backend/app/schemas/contact.py`
* `backend/app/schemas/data_source.py`
* `backend/app/schemas/background_job.py`
* `backend/tests/test_migration_definition.py`
* `backend/tests/test_models_metadata.py`

### Dependencies

* Existing Phase 1 database foundation
* Existing `contacts`, `data_sources`, and `background_jobs` tables
* `docs/data-model.md`
* `docs/database-erd.md`

### Acceptance Criteria

* `contacts.source_id` exists and references `data_sources.id`.
* `contacts.collection_timestamp` exists and is required for Phase 4 collected contacts.
* `ix_contacts_source_id` exists.
* `ix_contacts_collection_timestamp` exists.
* `uq_data_sources_business_source_url` exists on `(business_id, source_url)`.
* Contact partial unique indexes exist:
  * `ux_contacts_business_source_email`
  * `ux_contacts_business_source_phone`
  * `ux_contacts_business_source_name_url`
* Active-job idempotency index exists:
  * `ux_background_jobs_active_idempotency`
* Alembic migration applies cleanly from the current head.
* SQLAlchemy metadata matches the migration.

### Tests Required

* Migration applies successfully against PostgreSQL.
* Metadata test verifies new columns, foreign key, indexes, and constraints.
* Repository/model test verifies contacts can reference data sources.
* Duplicate data source insert for the same `(business_id, source_url)` is rejected.
* Duplicate active background job idempotency key is rejected for `pending` and `running`.
* Duplicate completed or failed job idempotency key is allowed when a new key is used.

## Step 2: Job Repository Layer

### Files Affected

* `backend/app/repositories/background_job_repository.py`
* `backend/app/repositories/base.py`
* `backend/app/schemas/background_job.py`
* `backend/app/models/background_job.py`
* `backend/tests/test_background_job_repository.py`

### Dependencies

* Step 1 active-job idempotency index
* Existing repository pattern
* `docs/job-queue-design.md`
* `docs/background-job-spec.md`

### Acceptance Criteria

* Repository can create `contact_collection`, `csv_export`, and `expired_refresh_token_cleanup` jobs.
* Job creation uses the standard payload envelope.
* Job creation is idempotent by `job_type` and `payload.idempotency_key`.
* Duplicate active job creation returns the existing job.
* Repository can fetch jobs by id.
* Repository can list eligible `pending` jobs where `retry_after` is null or due.
* Repository can atomically claim jobs using row-level locking semantics.
* Repository can update job status, attempts, lock fields, and sanitized error metadata.
* Repository never stores secrets, tokens, cookies, raw HTML, stack traces, or raw database errors in payload/error fields.

### Tests Required

* Create job with valid payload.
* Reject invalid job payload.
* Return existing duplicate active job.
* Claim one job once under concurrent claim attempts.
* Do not claim jobs with future `payload.retry_after`.
* Do not claim dead-lettered jobs.
* Update job completion.
* Update job failure metadata.
* Clear lock fields after completion or terminal failure.

## Step 3: Internal API Endpoints

### Files Affected

* `backend/app/api/internal.py`
* `backend/app/api/__init__.py`
* `backend/app/main.py`
* `backend/app/core/dependencies.py`
* `backend/app/core/permissions.py`
* `backend/app/core/exceptions.py`
* `backend/app/schemas/background_job.py`
* `backend/app/services/job_service.py`
* `backend/tests/test_internal_jobs_api.py`

### Dependencies

* Step 2 job repository
* Existing response wrapper utilities
* Existing request_id handling
* Existing RBAC helpers
* `INTERNAL_API_TOKEN`
* `docs/internal-api-contracts.md`
* `docs/rbac-permissions-matrix.md`

### Acceptance Criteria

* `POST /internal/v1/contact-collection` creates or returns a `contact_collection` job.
* `POST /internal/v1/csv-export` creates or returns a `csv_export` job.
* `GET /internal/v1/jobs/{job_id}` returns sanitized job status metadata.
* `POST /internal/v1/jobs/{job_id}/retry` creates a new retry job from an approved failed/dead-lettered job.
* `POST /internal/v1/jobs/{job_id}/cancel` cancels a cancellable pending or running job.
* All endpoints require `X-Internal-API-Token`.
* Valid internal token resolves to `system_worker`.
* Required worker RBAC permissions are enforced.
* All responses use the standard wrapper.
* All errors use the standard error wrapper.
* Internal endpoints never expose raw payload secrets, raw database errors, or stack traces.

### Tests Required

* Missing token returns `INTERNAL_AUTH_REQUIRED`.
* Invalid token returns `INTERNAL_AUTH_FORBIDDEN`.
* Missing `X-Request-ID` is rejected or assigned according to request_id middleware rules.
* Contact collection job creation succeeds.
* CSV export job creation succeeds.
* Duplicate job creation returns existing job.
* Job status response includes retry, cancellation, dead-letter, and error metadata.
* Retry endpoint creates a new job and preserves original job reference.
* Cancel endpoint marks job failed with `payload.cancelled = true`.
* Completed and dead-lettered jobs cannot be cancelled.

## Step 4: Worker Job Executor

### Files Affected

* `worker/main.py`
* `worker/config/settings.py`
* `worker/jobs/executor.py`
* `worker/jobs/handlers.py`
* `worker/jobs/payloads.py`
* `worker/jobs/status.py`
* `worker/tests/test_job_executor.py`
* `.env.example`
* `docker-compose.yml`

### Dependencies

* Step 2 job repository behavior
* Worker environment variables
* Existing worker health check
* `docs/job-queue-design.md`
* `docs/background-job-spec.md`
* `docs/deployment-guide.md`

### Acceptance Criteria

* Worker loads all required `WORKER_*` environment variables.
* Worker fails fast when required configuration is missing.
* Worker polls eligible jobs on the configured interval.
* Worker respects `WORKER_CONCURRENCY`.
* Worker claims jobs atomically.
* Worker dispatches only approved job types.
* Worker rejects unknown job types with `UNKNOWN_JOB_TYPE`.
* Worker records `background_job_claimed` and `background_job_started`.
* Worker logs include `request_id`, `job_id`, `job_type`, and `worker_id`.
* Worker never logs secrets, raw HTML, tokens, cookies, or private data.

### Tests Required

* Settings validation for required worker variables.
* Executor claims eligible job.
* Executor ignores jobs not yet due.
* Executor respects concurrency limit.
* Unknown job type fails safely.
* Handler dispatch invokes the expected job handler.
* Job execution logs include required structured fields.
* Worker health endpoint remains healthy.

## Step 5: Retry Handling

### Files Affected

* `worker/jobs/retry.py`
* `worker/jobs/executor.py`
* `backend/app/repositories/background_job_repository.py`
* `backend/app/schemas/background_job.py`
* `worker/tests/test_retry_handling.py`
* `backend/tests/test_background_job_repository.py`

### Dependencies

* Step 4 worker executor
* Canonical job error taxonomy
* `WORKER_DEFAULT_MAX_ATTEMPTS`
* `WORKER_RETRY_BASE_DELAY_SECONDS`
* `WORKER_RETRY_MAX_DELAY_SECONDS`

### Acceptance Criteria

* Retryable errors schedule retry by setting `status = "pending"` and `payload.retry_after`.
* Retry delay uses exponential backoff with configured base and max values.
* Attempts stop at `max_attempts`.
* Retryable failures at max attempts become dead-letter failures.
* Non-retryable failures do not retry.
* `background_job_retry_scheduled` is audit logged.
* `payload.last_error_code` and `payload.last_error_at` are updated.

### Tests Required

* `NETWORK_TIMEOUT` schedules retry.
* `DNS_FAILURE` schedules retry.
* `HTTP_429` schedules retry.
* `HTTP_5XX` schedules retry.
* `DB_CONFLICT` schedules retry.
* Non-retryable error does not schedule retry.
* Retry delay is capped by max delay.
* Job at max attempts is dead-lettered.
* Retry audit event is written.

## Step 6: Dead-Letter Handling

### Files Affected

* `worker/jobs/dead_letter.py`
* `worker/jobs/executor.py`
* `backend/app/repositories/background_job_repository.py`
* `backend/app/services/job_service.py`
* `worker/tests/test_dead_letter_handling.py`
* `backend/tests/test_internal_jobs_api.py`

### Dependencies

* Step 5 retry handling
* `docs/dead-letter-strategy.md`
* `docs/background-job-spec.md`

### Acceptance Criteria

* Terminal failures set `status = "failed"`.
* Dead-letter failures set `payload.dead_letter = true`.
* Dead-letter failures set sanitized `payload.dead_letter_reason`.
* Dead-letter handling updates `payload.last_error_code`.
* Dead-letter handling updates `payload.last_error_at`.
* Dead-letter handling clears `locked_at` and `locked_by`.
* Dead-letter handling writes `background_job_dead_lettered`.
* Dead-lettered jobs are not re-queued directly.
* Retry endpoint creates a new job rather than mutating the failed job to `pending`.

### Tests Required

* Invalid payload dead-letters.
* Prohibited source dead-letters.
* Robots denial dead-letters.
* Source authentication required dead-letters.
* Unknown job type dead-letters.
* Max attempts dead-letters.
* Dead-letter audit metadata contains job id, job type, attempts, max attempts, error code, and reason.
* Dead-letter metadata excludes secrets, raw HTML, stack traces, and raw database errors.
* Retry from dead-letter creates a new job.

## Step 7: Contact Collection Service

### Files Affected

* `worker/collectors/contact_collector.py`
* `worker/crawlers/public_page_client.py`
* `worker/jobs/contact_collection.py`
* `backend/app/services/contact_collection_service.py`
* `backend/app/repositories/contact_repository.py`
* `backend/app/repositories/data_source_repository.py`
* `backend/app/repositories/business_repository.py`
* `backend/app/core/security.py`
* `backend/app/schemas/contact.py`
* `backend/app/schemas/data_source.py`
* `worker/tests/test_contact_collection.py`
* `backend/tests/test_contact_repository.py`
* `backend/tests/test_data_source_repository.py`

### Dependencies

* Step 1 migration
* Step 4 worker executor
* Step 5 retry handling
* Step 6 dead-letter handling
* `ENCRYPTION_KEY`
* Compliance policy
* Contact traceability rules

### Acceptance Criteria

* Worker loads target business by `business_id`.
* Missing business fails with `BUSINESS_NOT_FOUND`.
* Worker resolves allowed source URLs from explicit sources, business website, or existing data sources.
* Worker enforces HTTP/HTTPS scheme.
* Worker rejects prohibited sources.
* Worker respects robots.txt where configured.
* Worker enforces domain rate limiting.
* Worker fetches only allowed public pages.
* Worker rejects unsupported content types.
* Worker does not store raw HTML.
* Worker extracts only explicitly published public contact fields.
* Worker writes or reuses `data_sources`.
* Every contact stores `business_id`, `source_id`, `source_url`, and `collection_timestamp`.
* `contacts.is_decision_maker` is always `false`.
* `contacts.priority_score` is always `0`.
* Email and phone are encrypted at the repository persistence boundary.
* Duplicate contacts are reused or treated as already completed.

### Tests Required

* Missing business returns `BUSINESS_NOT_FOUND`.
* Valid public contact page creates data source and contact.
* Contact has `business_id`, `source_id`, `source_url`, and `collection_timestamp`.
* Duplicate source URL reuses existing data source.
* Duplicate email contact does not create duplicate row.
* Duplicate phone fallback does not create duplicate row.
* Duplicate name/source fallback does not create duplicate row.
* Robots denial produces `ROBOTS_DENIED`.
* Prohibited source produces `PROHIBITED_SOURCE`.
* Authentication-required source produces `SOURCE_AUTH_REQUIRED`.
* Forbidden source produces `SOURCE_FORBIDDEN`.
* Unsupported content type produces `UNSUPPORTED_CONTENT_TYPE`.
* Raw HTML is not stored in job payload, logs, audit metadata, or database records.
* Email and phone are encrypted at rest and decrypted only for authorized reads.

## Step 8: Audit Logging

### Files Affected

* `backend/app/repositories/audit_log_repository.py`
* `backend/app/services/logging.py`
* `backend/app/services/job_service.py`
* `worker/jobs/executor.py`
* `worker/jobs/contact_collection.py`
* `worker/jobs/retry.py`
* `worker/jobs/dead_letter.py`
* `backend/tests/test_audit_logging.py`
* `worker/tests/test_worker_audit_logging.py`

### Dependencies

* Existing `audit_logs` table
* Existing request context and request_id handling
* Steps 2 through 7
* `docs/job-queue-design.md`
* `docs/contact-collection-design.md`

### Acceptance Criteria

* Job lifecycle events use canonical `background_job_*` names.
* Contact collection domain events use canonical `contact_collection_*` names.
* Every audit event includes `event_type`.
* Every audit event includes `request_id`.
* `user_id` is included when applicable.
* IP address is included when applicable.
* Job events include `metadata.job_id`.
* Job events include `metadata.job_type`.
* Worker events include `metadata.worker_id`.
* Audit metadata excludes secrets, tokens, cookies, raw HTML, raw stack traces, raw database errors, and private data.

### Tests Required

* `background_job_created` is written on job creation.
* `background_job_claimed` is written on claim.
* `background_job_started` is written on start.
* `background_job_completed` is written on success.
* `background_job_failed` is written on failure.
* `background_job_retry_scheduled` is written on retry.
* `background_job_dead_lettered` is written on dead-letter.
* `background_job_cancelled` is written on cancellation.
* Contact collection events are written for start, source checks, skipped sources, contact collection, source recording, completion, and failure.
* Audit metadata sanitization is verified.

## Step 9: Integration Tests

### Files Affected

* `backend/tests/test_phase_4a_migration.py`
* `backend/tests/test_internal_jobs_api.py`
* `backend/tests/test_background_job_repository.py`
* `backend/tests/test_contact_collection_integration.py`
* `backend/tests/test_phase_4a_security.py`
* `worker/tests/test_job_executor.py`
* `worker/tests/test_contact_collection.py`
* `worker/tests/test_retry_handling.py`
* `worker/tests/test_dead_letter_handling.py`
* `tests/test_phase_4a_docker_smoke.py`

### Dependencies

* Steps 1 through 8
* PostgreSQL test database
* Docker Compose environment variables
* Existing authentication and RBAC foundation

### Acceptance Criteria

* Full Phase 4A test suite passes.
* Internal APIs require `INTERNAL_API_TOKEN`.
* Internal APIs resolve identity to `system_worker`.
* Worker-specific RBAC permissions are enforced.
* Job lifecycle works end to end.
* Retry and dead-letter flows work end to end.
* Contact collection writes traceable contacts.
* Duplicate jobs and duplicate contacts are prevented.
* Audit events are written for all required actions.
* No MVP exclusions are implemented or exposed.

### Tests Required

* Internal contact collection job creation through API.
* Worker claims and completes a contact collection job.
* Worker writes contact and data source records.
* Worker handles retryable source failure.
* Worker dead-letters non-retryable failure.
* Internal retry endpoint creates a new job from a dead-lettered job.
* Internal cancel endpoint cancels eligible job.
* CSV export job creation creates one active job per export request.
* Concurrent duplicate job creation returns or preserves one active job.
* Audit log assertions for lifecycle and contact-domain events.
* Security assertions for token, RBAC, and sanitized output.

## Step 10: Docker Validation

### Files Affected

* `.env.example`
* `docker-compose.yml`
* `backend/Dockerfile`
* `worker/Dockerfile`
* `frontend/Dockerfile`
* `worker/config/settings.py`
* `backend/app/services/settings.py`
* `docs/phase-4a-validation-report.md`

### Dependencies

* Steps 1 through 9
* Docker
* Docker Compose
* Alembic migration command

### Acceptance Criteria

* `.env.example` includes all required Phase 4A worker variables.
* `docker-compose.yml` passes all worker variables to the worker service.
* PostgreSQL remains internal and has no public host port.
* Backend exposure remains development-only.
* `docker compose build` succeeds.
* `docker compose up -d` starts all services.
* PostgreSQL becomes healthy.
* Backend becomes healthy.
* Worker becomes healthy.
* Frontend remains healthy.
* Alembic migrations apply successfully.
* Phase 4A tests pass inside the containerized environment or against the Compose stack.
* Logs contain `request_id` and do not contain secrets.
* `docs/phase-4a-validation-report.md` is created after validation.

### Tests Required

* Docker build validation.
* Docker Compose health validation.
* Alembic migration validation.
* Backend health endpoint validation.
* Worker health endpoint validation.
* PostgreSQL network isolation validation.
* Internal API access validation from allowed network path.
* Internal API token rejection validation.
* Phase 4A integration test run.
* Log sanitization spot check.

## Implementation Order Rule

Steps must be implemented in order unless a later step is purely test scaffolding and does not require runtime behavior.

The Phase 4A implementation is not complete until:

* all acceptance criteria pass
* all required tests pass
* Docker validation passes
* `docs/phase-4a-validation-report.md` is produced
* no enrichment, scoring, decision-maker discovery, or LinkedIn people discovery functionality is introduced
