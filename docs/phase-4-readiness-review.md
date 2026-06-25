# Phase 4 Readiness Review

Date: 2026-06-25

Project: Lead Generator App

Scope: Documentation review only for Phase 4 Data Acquisition Engine readiness.

No application code was modified.

## Documents Reviewed

Requested documents:

* `docs/data-acquisition-strategy-v1.md`
* `docs/job-queue-design.md`
* `docs/background-job-spec.md`
* `docs/compliance-policy.md`
* `docs/security-standards.md`
* `docs/api-spec.md`
* `docs/data-model.md`
* `docs/project-structure.md`

Available and reviewed:

* `docs/data-acquisition-strategy-v1.md`
* `docs/job-queue-spec.md`
* `docs/compliance-policy.md`
* `docs/security-standards.md`
* `docs/api-spec.md`
* `docs/data-model.md`
* `docs/project-structure.md`

Missing requested documents:

* `docs/job-queue-design.md`
* `docs/background-job-spec.md`

## Executive Assessment

Phase 4 is not ready for implementation.

The documentation provides high-level direction for public-source acquisition, compliance, worker placement, PostgreSQL-backed jobs, and internal API naming. However, implementation-critical details are missing or inconsistent across the Phase 4 documentation set.

The main blockers are:

* Missing required job design documents.
* Incomplete job lifecycle and retry/dead-letter behavior.
* Phase scope conflicts around CSV export, enrichment, and scoring-adjacent intelligence.
* Insufficient internal API contracts.
* Insufficient database support for compliant contact-level source traceability.
* Missing worker configuration and environment-variable requirements.

## Critical Findings

### Critical 1: Required Phase 4 job design documents are missing

The requested review includes:

* `docs/job-queue-design.md`
* `docs/background-job-spec.md`

Neither file exists in `docs/`.

The repository currently has `docs/job-queue-spec.md`, but it is a brief V1 queue overview and does not replace the missing implementation documents.

Impact:

Phase 4 implementation cannot be considered ready because the core worker execution contract, lifecycle contract, retry rules, failure handling, dead-letter behavior, and payload contracts are not fully specified.

### Critical 2: Dead-letter strategy is not documented

The readiness checklist explicitly requires dead-letter strategy validation. No reviewed document defines:

* dead-letter state
* dead-letter table
* dead-letter transition rules
* dead-letter retention
* dead-letter replay policy
* operator visibility
* audit events for dead-lettered jobs

The `background_jobs` model in `data-model.md` supports only:

```text
pending
running
completed
failed
```

Impact:

Repeatedly failing acquisition jobs have no documented final quarantine path beyond `failed`. That is not sufficient for a robust worker system that must avoid repeated failed requests and preserve auditability.

## Major Findings

### Major 1: Job lifecycle is underspecified

`docs/job-queue-spec.md` states that workers poll `pending` jobs, lock before execution, mark jobs `running`, then mark them `completed` or `failed`.

Missing lifecycle requirements:

* atomic claim behavior
* lock timeout behavior
* stale `running` job recovery
* worker heartbeat behavior
* job idempotency requirements
* duplicate job prevention
* job priority or ordering
* job cancellation behavior
* job timeout behavior
* payload validation rules
* status transition table

Impact:

Multiple workers could be implemented inconsistently, and stuck jobs or duplicate acquisition jobs could corrupt data or create compliance risks.

### Major 2: Retry strategy is incomplete

`docs/job-queue-spec.md` states that workers update attempts and stop retrying after `max_attempts`.

Missing retry requirements:

* default `max_attempts`
* exponential backoff or fixed delay rules
* `next_run_at` or equivalent scheduling support
* retryable vs non-retryable error classification
* blocked-source retry behavior
* robots.txt denial retry behavior
* HTTP status retry matrix
* network timeout retry rules

Impact:

Phase 4 workers could repeatedly hit prohibited or blocked sources, violating compliance requirements to stop when blocked and avoid repeated failed requests.

### Major 3: Acquisition scope conflicts with current milestone boundaries

`docs/data-acquisition-strategy-v1.md` says Version 1 includes:

* business discovery
* website discovery
* public contact extraction
* email sourcing
* social profile collection
* CSV export

The same document also includes a "Data Enrichment Layer" with:

* communication intelligence
* social intelligence
* website intelligence
* CMS detection
* chatbot presence
* booking system detection
* technology stack
* analytics tools

Current project status places CSV export in a later milestone and prohibits enrichment/scoring during Phase 4.

Impact:

Phase 4 scope is ambiguous. An implementer could accidentally start CSV export, website intelligence, technology detection, or scoring-adjacent work during the data acquisition phase.

### Major 4: MVP job types do not match Phase 4 acquisition needs

`docs/job-queue-spec.md` lists required MVP job types:

```text
contact_collection
csv_export
expired_refresh_token_cleanup
```

Phase 4 Data Acquisition needs documentation for acquisition-specific jobs such as:

* business discovery
* website discovery
* contact page discovery
* public contact extraction
* source attribution
* social profile collection, if included in Phase 4

Impact:

The queue spec does not define the job types needed to implement the documented acquisition pipeline.

### Major 5: Internal API requirements are incomplete

`docs/api-spec.md` lists:

```text
POST /internal/v1/contact-collection
POST /internal/v1/csv-export
```

`docs/job-queue-spec.md` states internal routes must require `INTERNAL_API_TOKEN` and remain private.

Missing internal API requirements:

* request body schema
* response schema
* standard error codes
* required headers
* idempotency behavior
* job creation vs direct execution semantics
* RBAC or `system_worker` role behavior
* audit logging behavior
* rate limiting behavior
* health/status endpoints for workers

Impact:

Internal routes cannot be implemented consistently or safely from the current documentation.

### Major 6: Database support is incomplete for compliant contact source traceability

`docs/compliance-policy.md` requires every collected business or contact record to include:

* `source_type`
* `source_url`
* `trust_tier`
* `confidence_score`

`docs/data-model.md` gives `contacts`:

* `source_url`

But contacts do not include:

* `source_type`
* `trust_tier`
* `confidence_score`

Those fields exist on `data_sources`, but the data model does not define a contact-to-source relationship.

Impact:

Phase 4 cannot fully satisfy documented compliance requirements for contact-level traceability without either schema changes or a clarified source attribution model.

### Major 7: Audit logging requirements for worker and acquisition events are missing

`docs/security-standards.md` defines general audit requirements. Phase 4 docs do not define acquisition-specific audit events.

Missing audit requirements:

* job created
* job claimed
* job started
* job completed
* job failed
* job retried
* job dead-lettered
* source blocked
* robots.txt denied
* prohibited source skipped
* contact collected
* data source recorded

Impact:

Worker behavior may be operationally invisible and compliance-relevant events may not be traceable.

### Major 8: Worker configuration and environment variables are not defined

`docs/project-structure.md` lists general environment variables including `INTERNAL_API_TOKEN`, but Phase 4-specific worker configuration is not documented.

Missing configuration requirements:

* worker poll interval
* worker concurrency
* lock timeout
* job timeout
* default max attempts
* retry backoff settings
* HTTP request timeout
* per-domain request rate
* user agent
* robots.txt enforcement mode
* allowed source types
* blocked domains or source denylist

Impact:

Phase 4 behavior would rely on hardcoded values or inconsistent defaults, conflicting with the configuration-driven project standard.

### Major 9: Public source rules are not implementation-specific enough

`docs/compliance-policy.md` defines allowed and prohibited source categories. It does not define machine-enforceable rules for:

* robots.txt fetch and cache behavior
* per-domain throttling
* user-agent requirements
* max pages per business
* max redirects
* content type restrictions
* prohibited path handling
* blocked-source persistence

Impact:

The compliance policy is directionally correct, but it is not enough for consistent worker implementation.

### Major 10: Background job schema lacks scheduling and dead-letter support

`docs/data-model.md` defines `background_jobs` fields:

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

Missing fields or equivalent documented mechanisms:

* `request_id`
* `next_run_at`
* `started_at`
* `completed_at`
* `failed_at`
* `dead_lettered_at`
* `last_error_code`
* `priority`
* idempotency key

Impact:

The documented schema does not fully support reliable polling, delayed retries, observability, idempotency, or dead-letter transitions.

## Minor Findings

### Minor 1: API spec still includes CSV export as a V1 public endpoint

`docs/api-spec.md` documents:

```text
POST /api/v1/exports
```

CSV export is currently a later milestone and should not be part of Phase 4 implementation.

Impact:

This is a scope clarity issue for Phase 4 planning.

### Minor 2: Worker project structure includes future-oriented folders

`docs/project-structure.md` includes:

* `worker/enrichers/`
* `worker/scoring/`

These may remain as placeholders, but Phase 4 implementation should not add enrichment or scoring behavior.

Impact:

The structure may confuse implementation boundaries if Phase 4 scope is not clarified.

### Minor 3: API spec internal section numbering skips section 11

`docs/api-spec.md` jumps from section 10 to section 12.

Impact:

Documentation hygiene issue only.

### Minor 4: Documentation contains encoding artifacts

Some reviewed docs contain mojibake characters such as encoded dashes and checkmarks.

Impact:

Readability issue only. It does not block implementation by itself.

## Recommendations

### Recommendation 1: Create the missing Phase 4 implementation documents

Create:

* `docs/job-queue-design.md`
* `docs/background-job-spec.md`

These should either supersede or explicitly reference `docs/job-queue-spec.md`.

### Recommendation 2: Define a formal job state machine

Document allowed states, transitions, retry behavior, lock behavior, stale job recovery, and terminal states.

### Recommendation 3: Define a dead-letter strategy before implementation

Document whether dead-letter behavior uses:

* a new job state
* a dedicated dead-letter table
* metadata fields on `background_jobs`

### Recommendation 4: Resolve Phase 4 scope before implementation

Clarify whether Phase 4 includes only data acquisition or also any of:

* CSV export
* social profile collection
* website intelligence
* technology detection
* communication intelligence

### Recommendation 5: Align data model with compliance requirements

Either add contact-level source metadata or document how contacts map to `data_sources` records for source type, trust tier, and confidence score.

### Recommendation 6: Define worker environment variables

Add Phase 4 worker configuration to the documentation and `.env.example` before implementation begins.

### Recommendation 7: Define acquisition audit events

Document acquisition and worker audit events using `request_id`, `user_id` when applicable, worker identity, source URL, event type, and sanitized metadata.

## Readiness Validation By Area

| Area | Status | Assessment |
| --- | --- | --- |
| Worker architecture | Not ready | PostgreSQL polling is approved, but worker modules, claim semantics, concurrency, and observability are underspecified. |
| Job lifecycle | Not ready | Basic statuses exist, but no formal state machine exists. |
| Job states | Not ready | States are limited to `pending`, `running`, `completed`, `failed`; dead-letter and retry scheduling are undefined. |
| Retry strategy | Not ready | Attempts exist, but backoff, retryable errors, and scheduling are missing. |
| Failure handling | Not ready | Error message storage exists, but failure classification and recovery are missing. |
| Dead-letter strategy | Not ready | No dead-letter strategy is documented. |
| Acquisition workflows | Partially ready | High-level stages exist, but Phase 4 scope conflicts remain. |
| Public data source rules | Partially ready | Allowed/prohibited sources are defined, but enforcement details are missing. |
| Compliance requirements | Partially ready | Good policy baseline, but contact-level traceability is not fully supported by the data model. |
| Database support | Partially ready | Core tables exist, but job scheduling/dead-letter and contact traceability gaps remain. |
| Audit logging requirements | Not ready | General audit logging exists, but worker/acquisition event requirements are missing. |
| Internal API requirements | Not ready | Paths exist, but request/response/auth/error contracts are missing. |
| Security requirements | Partially ready | Strong general standards exist; worker-specific controls need more detail. |
| Configuration requirements | Not ready | Phase 4 worker configuration is not defined. |
| Environment variables | Not ready | `INTERNAL_API_TOKEN` exists, but acquisition and worker runtime variables are missing. |

## Final Readiness Assessment

Phase 4 Data Acquisition Engine is not ready for implementation.

Implementation should not begin until the Critical findings and Major findings are resolved in documentation. The project has a strong foundation from Phases 0 through 3, but Phase 4 requires more precise worker, queue, acquisition, compliance, internal API, and database contracts before code can be implemented safely.
