# Job Queue Design

Project: Lead Generator App

Status: Phase 4 MVP design.

## 1. Purpose

This document defines the V1 job queue architecture for Phase 4.

The queue uses the existing PostgreSQL `background_jobs` table and polling Python workers. No Redis, Celery, Kubernetes, or external queue service is introduced.

## 2. Approved Architecture

Components:

* FastAPI backend creates jobs.
* PostgreSQL stores jobs in `background_jobs`.
* Worker service polls PostgreSQL.
* Worker service claims jobs atomically.
* Worker service executes approved handlers.
* Worker service writes audit events.

Approved technologies:

* PostgreSQL
* SQLAlchemy
* Python async worker services
* Docker Compose private network

## 3. Job Table

The queue uses:

```text
background_jobs
```

Existing fields:

* `id`
* `job_type`
* `status`
* `payload`
* `attempts`
* `max_attempts`
* `locked_at`
* `locked_by`
* `error_message`
* `created_at`
* `updated_at`

Queue metadata must be stored inside `payload`.

Phase 4A may add database indexes and constraints required to enforce documented idempotency and contact traceability. It must not add a new queue table or new job status values.

## 4. Job Types

Approved MVP job types:

| Job type | Phase | Purpose |
| --- | --- | --- |
| `contact_collection` | Phase 4 | Collect public contact data and source attribution for businesses. |
| `csv_export` | Phase 4 | Generate CSV export files as a background task. |
| `expired_refresh_token_cleanup` | Security maintenance | Remove expired or retained revoked refresh tokens. |

Explicitly excluded from MVP jobs:

* decision-maker identification jobs
* opportunity scoring jobs
* AI enrichment jobs
* website intelligence jobs

## 5. Job States

Allowed database statuses:

```text
pending
running
completed
failed
```

State meanings:

| Status | Meaning |
| --- | --- |
| `pending` | Job is eligible for worker polling unless `payload.retry_after` is in the future. |
| `running` | Job has been claimed by one worker and is executing. |
| `completed` | Job finished successfully. |
| `failed` | Job reached a terminal failure or dead-letter condition. |

Dead-letter is represented as:

```json
{
  "dead_letter": true
}
```

inside `background_jobs.payload` with `status = "failed"`.

## 6. Job Payload Envelope

All jobs must use this payload envelope:

```json
{
  "schema_version": 1,
  "request_id": "...",
  "created_by_user_id": "uuid-or-null",
  "idempotency_key": "string",
  "retry_after": null,
  "dead_letter": false,
  "dead_letter_reason": null,
  "cancelled": false,
  "cancelled_reason": null,
  "source_id": null,
  "last_error_code": null,
  "last_error_at": null,
  "data": {}
}
```

Rules:

* `schema_version` is required.
* `request_id` is required.
* `idempotency_key` is required.
* `data` contains job-type-specific payload.
* Secrets, tokens, cookies, raw HTML, and raw database errors must never be stored.

## 6.1 Idempotency Enforcement

Job creation must be idempotent at the service/repository layer using `payload.idempotency_key`.

Rules:

* Contact collection idempotency key format: `contact_collection:{business_id}:{source_hash_or_discovery_mode}`.
* CSV export idempotency key format: `csv_export:{export_id}`.
* Before creating a job, the repository must check for an existing non-terminal job with the same `job_type` and `payload.idempotency_key`.
* Non-terminal statuses are `pending` and `running`.
* Race-safe enforcement must use a PostgreSQL partial unique index on active jobs:

```text
ux_background_jobs_active_idempotency
ON background_jobs (job_type, (payload->>'idempotency_key'))
WHERE status IN ('pending', 'running')
```

* If a duplicate non-terminal job exists, return the existing job instead of creating a new one.
* If a matching job is `completed` or `failed`, a new job may be created only with a new idempotency key.
* Retry-safe processing must use upsert or deduplication rules for contacts, data sources, and export files.
* One export request may have only one active `csv_export` job.

## 7. Polling And Claiming

Workers poll for jobs where:

* `status = "pending"`
* `payload.dead_letter` is not true
* `payload.retry_after` is null or not in the future

Workers must claim jobs atomically using a transaction and row-level locking.

Recommended SQL behavior:

```text
SELECT ... FOR UPDATE SKIP LOCKED
```

Claim operation:

1. Select one eligible job.
2. Set `status = "running"`.
3. Set `locked_at` to current timestamp.
4. Set `locked_by` to the worker id.
5. Increment `attempts`.
6. Commit before executing external requests.

## 8. Concurrency Rules

* A worker may process multiple jobs only up to configured concurrency.
* A job may be executed by only one worker at a time.
* Workers must not execute a job that is already `running` with a non-expired lock.
* Workers must not execute a job type without a registered handler.

## 9. Stale Lock Recovery

A `running` job is stale when:

```text
locked_at < now - WORKER_JOB_LOCK_TIMEOUT_SECONDS
```

Recovery rules:

* If attempts are below `max_attempts`, return the job to `pending`.
* If attempts are at or above `max_attempts`, mark the job `failed` with `payload.dead_letter = true`.
* Always write an audit event for stale lock recovery.

## 10. Retry Strategy

Default retry behavior:

* `max_attempts`: 3
* backoff: exponential
* base delay: `WORKER_RETRY_BASE_DELAY_SECONDS`
* maximum delay: `WORKER_RETRY_MAX_DELAY_SECONDS`

Retry delay is stored in:

```text
payload.retry_after
```

Retryable failures:

* network timeout
* DNS failure
* HTTP 429
* HTTP 500
* HTTP 502
* HTTP 503
* HTTP 504
* transient database conflict

Non-retryable failures:

* robots.txt denial
* explicit source block
* business not found
* source authentication required
* source forbidden
* unsupported content type
* invalid job payload
* prohibited source

## 11. Failure Handling

On failure, workers must:

1. classify the error
2. sanitize the error message
3. update `error_message`
4. update `payload.last_error_code`
5. update `payload.last_error_at`
6. decide retry or dead-letter
7. write an audit event

Workers must not store:

* raw HTML
* tokens
* cookies
* passwords
* stack traces
* raw database errors

## 12. Audit Events

Required job audit events:

* `background_job_created`
* `background_job_claimed`
* `background_job_started`
* `background_job_completed`
* `background_job_failed`
* `background_job_retry_scheduled`
* `background_job_cancelled`
* `background_job_dead_lettered`
* `background_job_stale_lock_recovered`

Contact collection domain events must use the `contact_collection_*` names defined in `contact-collection-design.md`. Domain events must not replace the required `background_job_*` lifecycle events.

Required audit fields:

* `event_type`
* `request_id`
* `user_id` when applicable
* `ip_address` when applicable
* `metadata.job_id`
* `metadata.job_type`
* `metadata.worker_id` when applicable

## 13. Worker Configuration

Required environment variables:

```text
WORKER_ID
WORKER_POLL_INTERVAL_SECONDS
WORKER_CONCURRENCY
WORKER_JOB_LOCK_TIMEOUT_SECONDS
WORKER_JOB_TIMEOUT_SECONDS
WORKER_DEFAULT_MAX_ATTEMPTS
WORKER_RETRY_BASE_DELAY_SECONDS
WORKER_RETRY_MAX_DELAY_SECONDS
WORKER_HTTP_TIMEOUT_SECONDS
WORKER_USER_AGENT
WORKER_ROBOTS_TXT_ENFORCEMENT
WORKER_DOMAIN_RATE_LIMIT_PER_MINUTE
INTERNAL_API_TOKEN
```

## 14. Security Requirements

Workers must:

* run inside the private Docker network
* use least privilege
* never expose public worker endpoints
* use `INTERNAL_API_TOKEN` for internal APIs
* resolve valid internal API token authentication to `system_worker`
* enforce worker-specific RBAC permissions for internal API actions
* never log secrets
* enforce compliance rules before fetching public sources
* attach `request_id` to logs and audit events

## 15. Definition Of Ready

The job queue is ready for implementation when:

* job payload schemas are defined
* job handlers are mapped
* retry and dead-letter behavior is documented
* internal API contracts are documented
* worker environment variables are documented
* audit events are documented
