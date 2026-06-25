# Internal API Contracts

Project: Lead Generator App

Status: Phase 4 MVP design.

## 1. Purpose

This document defines internal API contracts for worker-triggered and operational job workflows.

Internal APIs are not public APIs. They must use:

```text
/internal/v1/*
```

## 2. Security Requirements

Internal endpoints must:

* be reachable only on the private Docker network
* require `INTERNAL_API_TOKEN`
* reject requests without `X-Internal-API-Token`
* require `X-Request-ID`
* resolve successful internal authentication to the `system_worker` identity
* authorize worker-specific RBAC permissions
* use the standard response wrapper
* use the standard error wrapper
* never expose raw database errors
* never expose stack traces
* write audit events

Required headers:

```text
X-Internal-API-Token: <environment-provided-token>
X-Request-ID: <request-id>
Content-Type: application/json
```

Canonical internal security model:

| Layer | Requirement |
| --- | --- |
| Authentication | `INTERNAL_API_TOKEN` via `X-Internal-API-Token`. |
| Identity | Valid token resolves to `system_worker`. |
| Authorization | Endpoint checks the required `internal:*` RBAC permission. |
| Network | Endpoint is reachable only on the private Docker network. |

## 3. Standard Success Response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

## 4. Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description"
  },
  "request_id": "..."
}
```

## 5. Create Contact Collection Job

Endpoint:

```text
POST /internal/v1/contact-collection
```

Purpose:

Create a `contact_collection` background job.

Required permission:

```text
internal:contact_collection
```

Request:

```json
{
  "business_id": "uuid",
  "source_urls": [
    "https://example.com/contact"
  ],
  "discovery_mode": "business_contact_pages",
  "max_pages": 5,
  "idempotency_key": "contact_collection:business-id:business_contact_pages"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "job": {
      "id": "uuid",
      "job_type": "contact_collection",
      "status": "pending"
    }
  },
  "message": null,
  "request_id": "..."
}
```

Validation:

* `business_id` must be a UUID.
* `source_urls` must contain valid HTTP or HTTPS URLs when provided.
* `max_pages` must be between 1 and 10.
* `idempotency_key` is required and must follow `contact_collection:{business_id}:{source_hash_or_discovery_mode}`.
* Duplicate pending or running jobs with the same key return the existing job.
* Duplicate prevention must be race-safe through `ux_background_jobs_active_idempotency`.

Audit event:

```text
background_job_created
```

## 6. Create CSV Export Job

Endpoint:

```text
POST /internal/v1/csv-export
```

Purpose:

Create a `csv_export` background job. CSV export background processing is MVP.

Required permission:

```text
internal:csv_export
```

Request:

```json
{
  "export_id": "uuid",
  "idempotency_key": "csv_export:export-id"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "job": {
      "id": "uuid",
      "job_type": "csv_export",
      "status": "pending"
    }
  },
  "message": null,
  "request_id": "..."
}
```

Validation:

* `export_id` must be a UUID.
* `idempotency_key` is required and must follow `csv_export:{export_id}`.
* Exactly one active `csv_export` job may exist per export request.
* Duplicate prevention must be race-safe through `ux_background_jobs_active_idempotency`.

## 7. Get Job Status

Endpoint:

```text
GET /internal/v1/jobs/{job_id}
```

Purpose:

Return sanitized background job status for internal operational use.

Required permission:

```text
internal:job_read
```

Response:

```json
{
  "success": true,
  "data": {
    "job": {
      "id": "uuid",
      "job_type": "contact_collection",
      "status": "pending",
      "attempts": 0,
      "max_attempts": 3,
      "retry_after": null,
      "dead_letter": false,
      "dead_letter_reason": null,
      "cancelled": false,
      "cancelled_reason": null,
      "last_error_code": null,
      "last_error_at": null,
      "created_at": "2026-06-25T00:00:00Z",
      "updated_at": "2026-06-25T00:00:00Z"
    }
  },
  "message": null,
  "request_id": "..."
}
```

The response must not include raw payload data if it contains source URLs or operational metadata that is not needed by the caller.

## 8. Retry Dead-Lettered Job

Endpoint:

```text
POST /internal/v1/jobs/{job_id}/retry
```

Purpose:

Create a new job from a dead-lettered job after operator review.

Required permission:

```text
internal:job_retry
```

Rules:

* The original job remains `failed`.
* A new job is created with a new id.
* The new job must preserve a reference to the original job id inside payload metadata.
* The retry must write an audit event.

Response:

```json
{
  "success": true,
  "data": {
    "job": {
      "id": "new-job-uuid",
      "job_type": "contact_collection",
      "status": "pending",
      "retries_job_id": "old-job-uuid"
    }
  },
  "message": null,
  "request_id": "..."
}
```

## 9. Cancel Job

Endpoint:

```text
POST /internal/v1/jobs/{job_id}/cancel
```

Purpose:

Cancel a pending job or a running job that has not started irreversible work.

Rules:

* The caller must authenticate with `INTERNAL_API_TOKEN`.
* The resolved identity is `system_worker`.
* Required permission is `internal:job_cancel`.
* `completed` jobs cannot be cancelled.
* Dead-lettered jobs cannot be cancelled.
* Cancellation is represented with `status = "failed"` and `payload.cancelled = true`.
* Cancellation must write `background_job_cancelled`.

Request:

```json
{
  "reason": "operator_cancelled"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "job": {
      "id": "uuid",
      "status": "failed",
      "cancelled": true
    }
  },
  "message": null,
  "request_id": "..."
}
```

## 10. Error Codes

Internal APIs may return:

| HTTP status | Code | Meaning |
| --- | --- | --- |
| 400 | `INVALID_PAYLOAD` | Request body failed validation. |
| 401 | `INTERNAL_AUTH_REQUIRED` | Internal token missing. |
| 403 | `INTERNAL_AUTH_FORBIDDEN` | Internal token invalid. |
| 404 | `JOB_NOT_FOUND` | Job does not exist. |
| 404 | `BUSINESS_NOT_FOUND` | Target business for a contact collection job does not exist. |
| 409 | `JOB_DUPLICATE` | Idempotency key already exists. |
| 409 | `JOB_NOT_CANCELLABLE` | Job cannot be cancelled in its current state. |
| 429 | `RATE_LIMIT_EXCEEDED` | Internal request exceeded limit. |
| 500 | `INTERNAL_ERROR` | Sanitized internal error. |

Canonical job execution errors returned in job metadata:

```text
INVALID_PAYLOAD
BUSINESS_NOT_FOUND
PROHIBITED_SOURCE
ROBOTS_DENIED
SOURCE_AUTH_REQUIRED
SOURCE_FORBIDDEN
SOURCE_BLOCKED
UNSUPPORTED_CONTENT_TYPE
NETWORK_TIMEOUT
DNS_FAILURE
HTTP_429
HTTP_5XX
DB_CONFLICT
MAX_ATTEMPTS_EXCEEDED
JOB_NOT_FOUND
JOB_NOT_RETRYABLE
JOB_NOT_CANCELLABLE
JOB_CANCELLED
UNKNOWN_JOB_TYPE
```

## 11. Implementation Boundaries

Internal APIs may create and inspect jobs. They must not:

* perform public web crawling inside the request cycle
* bypass job queue execution
* expose internal database details
* start enrichment or scoring workflows
* return raw source content
