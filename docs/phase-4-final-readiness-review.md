# Phase 4 Final Readiness Review

Date: 2026-06-25

Project: Lead Generator App

Scope: Documentation validation review only.

No application code was modified.

## Documents Reviewed

Phase 4 design documents:

* `docs/job-queue-design.md`
* `docs/background-job-spec.md`
* `docs/internal-api-contracts.md`
* `docs/contact-collection-design.md`
* `docs/dead-letter-strategy.md`

Cross-reference documents:

* `docs/api-spec.md`
* `docs/data-model.md`
* `docs/architecture.md`
* `docs/project-structure.md`
* `docs/tech-stack.md`
* `docs/implementation-roadmap.md`

## Final Verdict

NOT READY FOR IMPLEMENTATION

Phase 4 has a strong design foundation, but implementation should not start until the Critical and Major findings below are resolved in documentation.

## Critical Findings

### Critical 1: CSV export background processing is inconsistent across MVP documentation

The validation rule says CSV export background processing is MVP.

Current contradictions:

* `job-queue-design.md` lists `csv_export` as an approved MVP job type, but labels its phase as "Future export milestone".
* `background-job-spec.md` says export generation may exist as a background job, but Phase 4 does not implement export features unless explicitly requested.
* `internal-api-contracts.md` defines `POST /internal/v1/csv-export`, but also says Phase 4 must not add export features unless explicitly requested.
* `implementation-roadmap.md` places export in a later Phase 8.

Impact:

An implementer cannot determine whether Phase 4 must implement the `csv_export` background job or only reserve its contract.

### Critical 2: Public contact collection is split between Phase 4 and a later roadmap phase

The validation rule says public contact collection is MVP.

Current contradictions:

* `contact-collection-design.md` defines Phase 4 public contact collection.
* `data-acquisition-strategy-v1.md` defines Phase 4 contact collection as MVP.
* `implementation-roadmap.md` says Phase 4 outputs business names, addresses, and websites.
* `implementation-roadmap.md` places email extraction, phone extraction, website crawling, and contact validation under Phase 5 Contact Enrichment System.

Impact:

The roadmap conflicts with the approved Phase 4 design. An implementer following the roadmap could omit the core public contact collection behavior required for Phase 4.

## Major Findings

### Major 1: Internal API contracts do not match `api-spec.md`

`internal-api-contracts.md` defines:

* `POST /internal/v1/contact-collection`
* `POST /internal/v1/csv-export`
* `GET /internal/v1/jobs/{job_id}`
* `POST /internal/v1/jobs/{job_id}/retry`

`api-spec.md` lists only:

* `POST /internal/v1/contact-collection`
* `POST /internal/v1/csv-export`

Impact:

Internal job status and dead-letter retry endpoints are documented in one file but absent from the canonical API specification.

### Major 2: Internal API security model is incomplete against broader security standards

`internal-api-contracts.md` requires:

* `X-Internal-API-Token`
* `X-Request-ID`

But `security-standards.md` and `api-spec.md` require protected endpoints to verify identity, role, and permissions. `api-spec.md` also names `system_worker` for internal pipelines.

Impact:

The documentation does not clearly define whether internal APIs require only the internal token, a `system_worker` identity, or both. This is a security contract gap.

### Major 3: Architecture still marks dead-letter handling as future

`dead-letter-strategy.md`, `job-queue-design.md`, and `background-job-spec.md` make dead-letter handling part of Phase 4.

`architecture.md` still says:

```text
Dead-letter job handling (future)
```

Impact:

Dead-letter behavior is both required and future-deferred depending on which document an implementer follows.

### Major 4: Job duplicate prevention is required but not enforceable from the documented data model

`background-job-spec.md` requires `payload.idempotency_key`.

`internal-api-contracts.md` defines `JOB_DUPLICATE`.

The existing `background_jobs` table has no documented `idempotency_key` column, unique constraint, or JSONB expression index. The design says metadata must remain in `payload`, but does not define how duplicates are reliably detected.

Impact:

Idempotent job creation is required by contract but lacks a clear enforcement mechanism.

### Major 5: Contact source traceability is documented but not database-enforced

`contact-collection-design.md` and `data-model.md` define contact source traceability through matching:

* `contacts.business_id`
* `contacts.source_url`
* `data_sources.business_id`
* `data_sources.source_url`

No documented foreign key, unique constraint, or join table enforces that a contact source URL has a corresponding `data_sources` row.

Impact:

The traceability model is understandable, but the database does not guarantee it. Implementation must add explicit repository/service validation or the docs must define a stronger schema contract.

### Major 6: Canonical job error taxonomy is missing `BUSINESS_NOT_FOUND`

`contact-collection-design.md` says a missing business should fail with:

```text
BUSINESS_NOT_FOUND
```

`background-job-spec.md` does not include `BUSINESS_NOT_FOUND` in the retryable or non-retryable error taxonomy.

Impact:

Failure handling for missing target businesses is specified in the workflow but missing from the canonical job error classification.

### Major 7: Roadmap phase names still imply enrichment for public contact collection

`implementation-roadmap.md` uses:

```text
Phase 5 — Contact Enrichment System
```

The approved MVP rules say AI enrichment is not MVP, while public contact collection is MVP.

Impact:

The term "enrichment" creates scope ambiguity even though later sections now reserve advanced intelligence and scoring.

## Minor Findings

### Minor 1: Dead-letter lock cleanup is left to implementation convention

`dead-letter-strategy.md` says the worker may clear or leave `locked_at` and `locked_by` for forensic review according to implementation convention.

Impact:

This is not a major blocker, but it leaves operational state inconsistent across possible implementations.

### Minor 2: Architecture diagram still includes a future scoring box

`architecture.md` still includes a "Future Scoring" box in the high-level system diagram.

Impact:

The box is labeled future, so it does not directly add MVP functionality, but it is visually confusing in a Phase 4 readiness context.

### Minor 3: Project structure database standard conflicts with existing table definitions

`project-structure.md` says every table should have:

```text
created_at
updated_at
```

`data-model.md` documents several tables without `updated_at`, including contact/source/audit-style records.

Impact:

This is a pre-existing documentation inconsistency. It does not uniquely block Phase 4 but should be cleaned up before strict schema validation.

### Minor 4: Contact collection audit event names differ from generic job audit event names

`job-queue-design.md` defines generic job audit events such as:

* `background_job_started`
* `background_job_completed`
* `background_job_failed`

`contact-collection-design.md` defines domain events such as:

* `contact_collection_started`
* `contact_collection_completed`
* `contact_collection_failed`

Impact:

Both sets may be valid, but the docs do not state whether both must be written or whether domain events replace generic job events.

## Validation By Objective

| Objective | Result | Notes |
| --- | --- | --- |
| Identify contradictions | Failed | Critical contradictions remain around CSV export background processing and public contact collection phase ownership. |
| Identify missing fields/tables | Partial | No new tables are required by design, but idempotency and contact traceability lack enforceable schema support. |
| Identify security gaps | Failed | Internal API identity, role, permission, and token requirements are not fully reconciled. |
| Identify worker/backend API contract mismatches | Failed | `internal-api-contracts.md` has endpoints absent from `api-spec.md`. |
| Verify contact source traceability | Partial | Traceability is defined by source URL matching, but not database-enforced. |
| Verify dead-letter workflow consistency | Failed | Dead-letter is Phase 4 in design docs but future in architecture. |
| Verify retry logic consistency | Passed with minor caveat | Retryable/non-retryable logic is broadly consistent; `BUSINESS_NOT_FOUND` is missing from canonical taxonomy. |
| Verify MVP scope compliance | Failed | Public contact collection and CSV export background processing are not consistently represented as MVP across docs. |

## MVP Scope Validation

| Rule | Result | Evidence |
| --- | --- | --- |
| Decision-maker identification is not MVP | Passed | Phase 4 design docs consistently exclude it. |
| Opportunity scoring is not MVP | Passed | Phase 4 design docs consistently exclude it. |
| AI enrichment is not MVP | Passed | Phase 4 design docs consistently exclude it. |
| Public contact collection is MVP | Failed | Design docs include it, but `implementation-roadmap.md` places core contact work in a later phase. |
| CSV export background processing is MVP | Failed | Queue/internal API docs mention `csv_export`, but multiple docs label it future or not implemented unless requested. |

## Required Documentation Fixes Before Implementation

1. Make CSV export background processing consistently MVP or explicitly move it out of MVP everywhere.
2. Update `implementation-roadmap.md` so Phase 4 includes public contact collection and does not defer it to a contact enrichment phase.
3. Add `GET /internal/v1/jobs/{job_id}` and `POST /internal/v1/jobs/{job_id}/retry` to `api-spec.md`, or remove them from `internal-api-contracts.md`.
4. Define internal API authentication as token-only, `system_worker` identity, or both.
5. Update `architecture.md` so dead-letter handling is Phase 4, not future.
6. Define duplicate job enforcement for `idempotency_key`.
7. Define whether contact source traceability is enforced in application logic or through schema changes.
8. Add `BUSINESS_NOT_FOUND` to the canonical job error taxonomy.
9. Clarify whether generic job audit events and contact-collection domain audit events are both required.

## Final Assessment

Phase 4 is not ready for implementation.

The documentation is close, but the remaining contradictions affect implementation scope, API surface, worker security, job idempotency, and dead-letter consistency. These should be resolved in documentation before code work begins.
