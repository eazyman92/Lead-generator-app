# Dead-Letter Strategy

Project: Lead Generator App

Status: Phase 4 MVP design.

## 1. Purpose

This document defines how Phase 4 handles terminal background job failures.

Phase 4 uses the existing `background_jobs` table. It does not introduce a new dead-letter table or a new database status.

## 2. Dead-Letter Representation

A dead-lettered job is represented as:

```text
background_jobs.status = "failed"
```

and:

```json
{
  "dead_letter": true,
  "dead_letter_reason": "sanitized reason"
}
```

inside `background_jobs.payload`.

## 3. Dead-Letter Conditions

A job must be dead-lettered when:

* attempts reach `max_attempts`
* payload is invalid
* source is prohibited
* robots.txt denies collection
* source explicitly blocks automated access
* source requires authentication
* job type is unknown
* stale lock recovery exceeds allowed attempts
* handler raises a non-retryable compliance error

## 4. Non-Dead-Letter Failures

Retryable failures should not immediately dead-letter unless attempts are exhausted.

Retryable examples:

* network timeout
* DNS failure
* HTTP 429
* HTTP 500
* HTTP 502
* HTTP 503
* HTTP 504

## 5. Transition Flow

Dead-letter flow:

1. Worker detects terminal failure.
2. Worker sanitizes error code and message.
3. Worker updates `error_message`.
4. Worker updates `payload.last_error_code`.
5. Worker updates `payload.last_error_at`.
6. Worker sets `payload.dead_letter = true`.
7. Worker sets `payload.dead_letter_reason`.
8. Worker sets `status = "failed"`.
9. Worker clears `locked_at` and `locked_by` after writing sanitized failure metadata.
10. Worker writes `background_job_dead_lettered` audit event.

## 6. Audit Logging

Required event:

```text
background_job_dead_lettered
```

Required metadata:

* `job_id`
* `job_type`
* `worker_id`
* `attempts`
* `max_attempts`
* `error_code`
* `dead_letter_reason`

Audit metadata must not include:

* secrets
* tokens
* cookies
* raw HTML
* raw stack traces
* private data

## 7. Operator Review

Dead-lettered jobs require review before retry.

Operator review must verify:

* source is allowed
* retry will not violate compliance policy
* payload is valid
* failure is understood
* no private or prohibited data was stored

## 8. Replay Strategy

Dead-lettered jobs must not be changed back to `pending`.

If retry is approved:

1. Create a new job.
2. Copy only sanitized and valid payload fields.
3. Set a new `idempotency_key`.
4. Store original job id in payload metadata.
5. Write an audit event.

## 9. Retention

Dead-lettered jobs should be retained for operational review for at least 90 days unless a stricter retention policy applies.

Retention cleanup must preserve audit logs.

## 10. Reporting

Operational reporting should count:

* dead-lettered jobs by job type
* dead-lettered jobs by reason
* repeated source blocks
* repeated robots.txt denials
* retry exhaustion events

## 11. Implementation Boundaries

Dead-letter handling must not:

* introduce new infrastructure
* create a new queue table
* create enrichment workflows
* create scoring workflows
* retry prohibited sources automatically
