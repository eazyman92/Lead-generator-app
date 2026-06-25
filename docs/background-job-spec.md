# Background Job Specification

Project: Lead Generator App

Status: Phase 4 MVP specification.

## 1. Purpose

This document defines the canonical background job lifecycle, payload contracts, failure behavior, and worker responsibilities for MVP implementation.

## 2. Canonical Job Record

Database table:

```text
background_jobs
```

All jobs must use the existing table. Phase 4 must not introduce a new queue database table.

## 3. Job Status Lifecycle

Allowed statuses:

```text
pending
running
completed
failed
```

Allowed transitions:

| From | To | Reason |
| --- | --- | --- |
| none | `pending` | Job created. |
| `pending` | `running` | Worker claimed job. |
| `running` | `completed` | Handler completed successfully. |
| `running` | `pending` | Retry scheduled. |
| `running` | `failed` | Terminal failure or dead-letter. |
| `pending` | `failed` | Invalid payload or cancellation before execution. |
| `running` | `failed` | Cancellation accepted before irreversible work starts. |
| `running` | `failed` | Stale lock exceeded attempts. |

Disallowed transitions:

* `completed` to any other status
* `failed` to any other status unless an explicit operator retry creates a new job
* `running` to `running`
* `pending` to `completed`

## 4. Payload Envelope

Required payload fields:

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `schema_version` | integer | Yes | Payload schema version. |
| `request_id` | string | Yes | Request trace id. |
| `created_by_user_id` | UUID or null | Yes | User that caused the job, if any. |
| `idempotency_key` | string | Yes | Duplicate prevention key. |
| `retry_after` | timestamp or null | Yes | Earliest retry time. |
| `dead_letter` | boolean | Yes | Marks terminal dead-letter failure. |
| `dead_letter_reason` | string or null | Yes | Sanitized dead-letter reason. |
| `cancelled` | boolean | Yes | Marks operator cancellation. |
| `cancelled_reason` | string or null | Yes | Sanitized cancellation reason. |
| `source_id` | UUID or null | No | Source record associated with source-specific work. |
| `last_error_code` | string or null | Yes | Sanitized error code. |
| `last_error_at` | timestamp or null | Yes | Last failure timestamp. |
| `data` | object | Yes | Job-specific data. |

## 5. Contact Collection Payload

Job type:

```text
contact_collection
```

Payload `data`:

```json
{
  "business_id": "uuid",
  "source_urls": [
    "https://example.com/contact"
  ],
  "discovery_mode": "business_contact_pages",
  "max_pages": 5
}
```

Rules:

* `business_id` is required.
* `source_urls` may be empty only when the job is allowed to discover contact pages from the business website.
* `max_pages` must be bounded.
* The worker must not use the job to perform decision-maker identification.

## 6. CSV Export Payload

Job type:

```text
csv_export
```

Export generation is an MVP background job. The public export request creates an export record, and the worker processes one `csv_export` job for that export.

Payload `data`:

```json
{
  "export_id": "uuid"
}
```

Rules:

* `export_id` is required.
* Exactly one active `csv_export` job may exist for one export request.
* The idempotency key must use `csv_export:{export_id}`.
* Export output must not include fields outside the permitted MVP export contract.

## 6.1 Idempotency Rules

Contact collection:

* Use unique job keys based on `business_id` and source set or discovery mode.
* Duplicate `pending` or `running` contact collection jobs must return the existing job.
* Contact writes must be retry-safe and deduplicate by business plus email, phone, or source-backed name.
* Race-safe duplicate prevention must use the partial unique index `ux_background_jobs_active_idempotency` on `background_jobs (job_type, payload->>'idempotency_key')` where `status IN ('pending', 'running')`.

CSV export:

* Use one export job per export request.
* Duplicate `pending` or `running` export jobs must return the existing job.
* Export file generation must be retry-safe and overwrite or resume only the file associated with the same `export_id`.
* The same active-job idempotency index enforces one active `csv_export` job per `csv_export:{export_id}` key.

## 7. Refresh Token Cleanup Payload

Job type:

```text
expired_refresh_token_cleanup
```

Payload `data`:

```json
{
  "retention_days": 90
}
```

## 8. Worker Responsibilities

Workers must:

* poll for eligible `pending` jobs
* claim jobs atomically
* validate payload before execution
* execute only approved job types
* enforce job timeout
* enforce source compliance rules
* update job status
* write audit events
* sanitize errors
* schedule retries
* dead-letter terminal failures

Workers must not:

* execute unknown job types
* store secrets in payload
* store raw HTML in payload
* collect private data
* infer decision-maker status
* perform opportunity scoring
* perform AI enrichment

## 9. Retry Classification

Retryable:

| Error code | Meaning |
| --- | --- |
| `NETWORK_TIMEOUT` | Public source request timed out. |
| `DNS_FAILURE` | Source host could not be resolved. |
| `HTTP_429` | Public source rate limited. |
| `HTTP_5XX` | Public source server error. |
| `DB_CONFLICT` | Retryable database conflict. |

Non-retryable:

| Error code | Meaning |
| --- | --- |
| `ROBOTS_DENIED` | robots.txt disallows collection. |
| `SOURCE_BLOCKED` | Source blocked or forbids automation. |
| `SOURCE_AUTH_REQUIRED` | Source requires authentication, including HTTP 401. |
| `SOURCE_FORBIDDEN` | Source forbids access, including HTTP 403. |
| `BUSINESS_NOT_FOUND` | Target business does not exist. |
| `PROHIBITED_SOURCE` | Source violates compliance policy. |
| `INVALID_PAYLOAD` | Job payload failed validation. |
| `UNSUPPORTED_CONTENT_TYPE` | Source returned unsupported content. |
| `JOB_CANCELLED` | Job was cancelled by an authorized internal request. |

## 10. Completion Rules

A job may be marked `completed` only when:

* payload validation passed
* handler completed without terminal error
* database writes were committed
* audit logging was attempted
* no prohibited source data was stored

## 11. Failure Rules

A job must be marked `failed` when:

* attempts reach `max_attempts`
* error is non-retryable
* payload is invalid
* source is prohibited
* stale lock recovery exceeds retry allowance
* cancellation is accepted

For dead-letter failures:

* `status = "failed"`
* `payload.dead_letter = true`
* `payload.dead_letter_reason` contains a sanitized reason

For cancelled jobs:

* `status = "failed"`
* `payload.cancelled = true`
* `payload.cancelled_reason` contains a sanitized reason
* `payload.dead_letter = false`

## 12. Observability

Worker logs must include:

* timestamp
* service
* level
* message
* request_id
* job_id
* job_type
* worker_id

Logs must not include:

* passwords
* tokens
* cookies
* raw HTML
* private data
* stack traces in user-facing metadata

## 13. Test Requirements

Phase 4 implementation tests must cover:

* job creation
* job claim behavior
* payload validation
* successful completion
* retryable failure
* non-retryable failure
* dead-letter marking
* stale lock recovery
* audit event creation
* compliance source rejection
