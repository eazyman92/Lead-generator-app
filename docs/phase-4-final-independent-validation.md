# Phase 4 Final Independent Validation

Date: 2026-06-25

Project: Lead Generator App

Scope: Independent readiness validation for Phase 4A implementation. This review treated prior readiness reports as non-authoritative and validated active documentation plus Phase 4-relevant repository schema evidence.

No application code was modified.

## Critical Blockers

### 1. Contact source traceability is not implementable against the current documented and migrated schema

Active Phase 4 documents require every collected contact to store:

* `business_id`
* `source_id`
* `collection_timestamp`

`data-model.md`, `api-spec.md`, `contact-collection-design.md`, and `data-acquisition-strategy-v1.md` now describe this as canonical.

However, `database-erd.md` and the current migration/model evidence still show `contacts` without:

* `source_id`
* `collection_timestamp`
* foreign key from `contacts.source_id` to `data_sources.id`
* indexes on `contacts.source_id` and `contacts.collection_timestamp`

This means Phase 4 contact collection cannot satisfy the documented traceability requirement without a schema/model/migration change. It also means `database-erd.md` conflicts with `data-model.md`.

### 2. Phase 4 schema-change policy conflicts with the required contact traceability fields

`job-queue-design.md` states that Phase 4 must not require schema changes and must store additional queue metadata in `background_jobs.payload`.

That is valid for queue metadata, but Phase 4 contact traceability requires contact-table fields that do not exist in the current ERD/migration/model. The documentation does not clearly authorize or scope the required migration for `contacts.source_id` and `contacts.collection_timestamp`.

Until this is resolved, implementers must guess whether Phase 4A is allowed to alter the database schema.

## Major Issues

### 1. Idempotency rules are not enforceable under concurrency as documented

The docs require idempotent job creation using `payload.idempotency_key`, but the active schema documents no generated column, unique index, partial unique index, or locking strategy that prevents duplicate `pending` or `running` jobs under concurrent requests.

The repository-layer lookup rule is useful but not sufficient by itself for race-safe enforcement.

### 2. Contact and data-source deduplication requirements lack documented uniqueness constraints

The docs require workers to reuse existing `data_sources` rows and avoid duplicate contacts, but `database-erd.md` documents no unique constraints for:

* data source identity such as `(business_id, source_url)`
* contact identity such as `(business_id, source_id, email)` or an approved equivalent

The deduplication algorithm is described conceptually, but enforceable database rules are missing.

### 3. Audit event names are inconsistent across active documents

The job queue docs use events such as:

* `background_job_created`
* `background_job_started`
* `background_job_completed`
* `background_job_failed`
* `background_job_dead_lettered`

The acquisition/contact docs also use:

* `contact_collection_job_created`
* `contact_collection_started`
* `contact_collection_completed`
* `contact_collection_failed`

The audit requirements are supportable by `audit_logs`, but the canonical event taxonomy is not fully aligned.

### 4. Internal job status response is inconsistent

`api-spec.md` says `GET /internal/v1/jobs/{job_id}` returns status, attempts, retry metadata, cancellation metadata, and dead-letter metadata.

`internal-api-contracts.md` shows a minimal response with status, attempts, max attempts, dead-letter, created_at, and updated_at, but omits retry and cancellation fields.

The endpoint exists, but implementers must infer the complete response shape.

### 5. Job error taxonomy is not fully canonical

Error naming differs across active docs:

* `api-spec.md` uses `INVALID_PAYLOAD`
* `internal-api-contracts.md` uses `INVALID_JOB_PAYLOAD`
* `api-spec.md` lists `SOURCE_AUTH_REQUIRED`
* `background-job-spec.md` uses `HTTP_401`

`BUSINESS_NOT_FOUND` is present, but the full job error vocabulary still has drift.

### 6. Worker environment variables are documented but not wired into current Compose/environment templates

`job-queue-design.md` and `project-structure.md` require worker variables such as:

* `WORKER_ID`
* `WORKER_POLL_INTERVAL_SECONDS`
* `WORKER_CONCURRENCY`
* `WORKER_JOB_LOCK_TIMEOUT_SECONDS`
* `WORKER_JOB_TIMEOUT_SECONDS`
* `WORKER_DEFAULT_MAX_ATTEMPTS`
* `WORKER_RETRY_BASE_DELAY_SECONDS`
* `WORKER_RETRY_MAX_DELAY_SECONDS`
* `WORKER_HTTP_TIMEOUT_SECONDS`
* `WORKER_USER_AGENT`
* `WORKER_ROBOTS_TXT_ENFORCEMENT`
* `WORKER_DOMAIN_RATE_LIMIT_PER_MINUTE`

The current `.env.example` and `docker-compose.yml` do not provide or pass those variables to the worker service. Docker Compose implementation can begin, but the documented Phase 4 worker runtime cannot be configured without additional environment updates.

### 7. Contact data encryption requirement is unresolved for Phase 4

`api-spec.md` and `security-standards.md` require sensitive fields such as contact emails and contact data to be encrypted at rest.

The database/model documentation does not define how Phase 4 contact collection should encrypt or decrypt contact fields, where encryption is applied, or which repository/service owns that responsibility.

## Minor Issues

### 1. `database-erd.md` still labels its scope as Phase 3

The ERD says its scope is current database foundation through Phase 3 remediation. Since Phase 4 readiness depends on database traceability fields, the ERD being stale increases implementation risk.

### 2. Compliance traceability wording is less precise than the data model

`compliance-policy.md` says every collected business or contact record must include `source_type`, `source_url`, `trust_tier`, and `confidence_score`.

The newer canonical model stores those fields on `data_sources` and links contacts through `source_id`. This is conceptually compatible, but the wording should align with the source-reference model.

### 3. Worker repository contains future-scope placeholder folders

The active docs exclude enrichment and scoring from Phase 4, but the repository contains `worker/enrichers/` and `worker/scoring/` placeholders. This is not a functional blocker, but it can confuse Phase 4 implementation boundaries.

### 4. Operational monitoring requirements are high-level

`deployment-guide.md` defines worker metrics such as jobs completed, jobs failed, and retry count, but the Phase 4 docs do not specify whether those are log-derived, endpoint-derived, or database-query-derived for MVP.

## Recommendations

### 1. Add an explicit Phase 4A database migration scope

Before implementation, document and then implement the required schema/model migration for:

* `contacts.source_id`
* `contacts.collection_timestamp`
* FK `contacts.source_id -> data_sources.id`
* indexes for `contacts.source_id` and `contacts.collection_timestamp`

### 2. Define enforceable idempotency constraints

Document a race-safe strategy for active job uniqueness. Acceptable options include:

* generated idempotency column plus partial unique index
* explicit table-level constraint support
* transactional advisory lock strategy

### 3. Define source/contact uniqueness rules

Document the canonical uniqueness rules for:

* `data_sources`
* collected contacts
* CSV export job linkage

### 4. Normalize audit event names

Create one canonical Phase 4 audit event list and reference it from queue, contact collection, acquisition, and dead-letter docs.

### 5. Normalize job error codes

Use one canonical error taxonomy across `api-spec.md`, `background-job-spec.md`, `internal-api-contracts.md`, and `job-queue-design.md`.

### 6. Update worker environment wiring

Add the required worker settings to `.env.example` and pass them through `docker-compose.yml` before Phase 4A implementation begins.

### 7. Define Phase 4 contact-field encryption ownership

Document whether encryption occurs in services, repositories, model types, or database utilities, and how search/export code reads encrypted contact fields safely.

## Final Verdict

NOT READY FOR IMPLEMENTATION
