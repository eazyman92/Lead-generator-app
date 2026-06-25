# Job Queue Specification (V1)

Project: Lead Generator App

Status: Canonical queue overview. Detailed implementation contracts are defined in:

* `job-queue-design.md`
* `background-job-spec.md`
* `dead-letter-strategy.md`
* `internal-api-contracts.md`

## 1. Purpose

This document defines the approved V1 background job system.

V1 uses PostgreSQL-backed jobs and polling workers. No external queue is required.

## 2. Approved Technology

Use:

* PostgreSQL
* SQLAlchemy
* Python async worker services

Do not introduce Redis, Celery, Kubernetes, or another queue system in V1.

## 3. Job Table

The job table is:

```text
background_jobs
```

Required fields are defined in `data-model.md`.

Additional queue metadata is stored in the JSONB `payload` field as defined in `background-job-spec.md`.

## 4. Job Statuses

Allowed database statuses:

```text
pending
running
completed
failed
```

Dead-lettered jobs use:

```text
status = failed
payload.dead_letter = true
```

## 5. Worker Behavior

Workers must:

* poll for eligible `pending` jobs
* claim jobs atomically with row-level locking
* update status to `running`
* execute only approved job handlers
* update status to `completed` on success
* update attempts and sanitized error metadata on failure
* schedule retries using `payload.retry_after`
* stop retrying after `max_attempts`
* dead-letter terminal failures
* write audit events
* use `request_id`

## 6. Internal API Routes

Internal worker routes use:

```text
/internal/v1/*
```

Internal routes must:

* never be publicly exposed
* require `INTERNAL_API_TOKEN`
* resolve successful token validation to the `system_worker` identity
* enforce worker-specific RBAC permissions
* require `X-Request-ID`
* be available only on the private Docker network
* follow `internal-api-contracts.md`

## 7. MVP Job Types

Approved MVP job types:

```text
contact_collection
csv_export
expired_refresh_token_cleanup
```

Notes:

* `contact_collection` is the Phase 4 acquisition job.
* `csv_export` is the MVP CSV export generation job.
* `expired_refresh_token_cleanup` is a security maintenance job.

Idempotency rules:

* Contact collection jobs use unique job keys based on `business_id` and source set or discovery mode.
* Duplicate pending or running contact collection jobs return the existing job.
* Contact writes must be retry-safe and deduplicate public contacts by business and source-backed contact identifiers.
* CSV export creates one active `csv_export` job per export request using `csv_export:{export_id}`.
* Duplicate pending or running CSV export job creation returns the existing job.

Explicitly excluded from MVP:

* decision-maker identification jobs
* opportunity scoring jobs
* AI enrichment jobs
* website intelligence jobs

## 8. Configuration

Worker runtime configuration must come from environment variables documented in `job-queue-design.md`.

No queue behavior may depend on hardcoded secrets or hidden constants.
