# Phase 4 Remediation Report

Date: 2026-06-25

Project: Lead Generator App

Scope: Documentation remediation only. No application code was modified.

## Purpose

This report documents remediation of the findings from `docs/phase-4-final-readiness-review.md`.

## Remediated Findings

### 1. CSV Export Scope

Canonical decision:

* CSV export background processing is MVP.
* Export generation runs as a `csv_export` background job.
* Advanced enrichment, decision-maker identification, and opportunity scoring remain excluded from MVP.

Updated documents:

* `docs/api-spec.md`
* `docs/architecture.md`
* `docs/background-job-spec.md`
* `docs/implementation-roadmap.md`
* `docs/internal-api-contracts.md`
* `docs/job-queue-design.md`
* `docs/job-queue-spec.md`
* `docs/phase-4-design-readiness-report.md`

### 2. Public Contact Collection Scope

Canonical decision:

* Public contact collection is Phase 4 MVP.
* Contact collection occurs through background jobs.
* Public website information only.
* No decision-maker identification.
* No LinkedIn people discovery.
* No enrichment.
* No scoring.

Updated documents:

* `docs/architecture.md`
* `docs/contact-collection-design.md`
* `docs/data-acquisition-strategy-v1.md`
* `docs/implementation-roadmap.md`

### 3. Internal API Alignment

Internal APIs now consistently document:

* `POST /internal/v1/contact-collection`
* `POST /internal/v1/csv-export`
* `GET /internal/v1/jobs/{job_id}`
* `POST /internal/v1/jobs/{job_id}/retry`
* `POST /internal/v1/jobs/{job_id}/cancel`

Updated documents:

* `docs/api-spec.md`
* `docs/internal-api-contracts.md`
* `docs/rbac-permissions-matrix.md`

### 4. Internal Security Model

Canonical model:

* Authentication: `INTERNAL_API_TOKEN`
* Identity: `system_worker`
* Authorization: worker-specific RBAC permissions

Updated documents:

* `docs/api-spec.md`
* `docs/architecture.md`
* `docs/internal-api-contracts.md`
* `docs/job-queue-design.md`
* `docs/job-queue-spec.md`
* `docs/rbac-permissions-matrix.md`

### 5. Dead-Letter Handling

Canonical decision:

* Dead-letter processing is MVP.
* Dead-letter queue behavior is part of the background job system.
* Dead-lettered jobs use `background_jobs.status = "failed"` and `payload.dead_letter = true`.

Updated documents:

* `docs/architecture.md`
* `docs/background-job-spec.md`
* `docs/dead-letter-strategy.md`
* `docs/job-queue-design.md`
* `docs/job-queue-spec.md`

### 6. Idempotency Enforcement

Documented enforcement:

* Contact collection jobs use unique keys based on `business_id` and source set or discovery mode.
* Duplicate pending or running contact collection jobs return the existing job.
* Contact processing must be retry-safe and deduplicate persisted contacts.
* CSV export uses one active `csv_export` job per export request.
* CSV export idempotency keys use `csv_export:{export_id}`.

Updated documents:

* `docs/background-job-spec.md`
* `docs/contact-collection-design.md`
* `docs/internal-api-contracts.md`
* `docs/job-queue-design.md`
* `docs/job-queue-spec.md`

### 7. Contact Source Traceability

Canonical implementation:

Every collected contact must be traceable to:

* `business_id`
* `source_id`
* `collection_timestamp`

Updated documents:

* `docs/api-spec.md`
* `docs/architecture.md`
* `docs/contact-collection-design.md`
* `docs/data-acquisition-strategy-v1.md`
* `docs/data-model.md`
* `docs/phase-4-design-readiness-report.md`

### 8. Error Taxonomy

Added canonical job error:

```text
BUSINESS_NOT_FOUND
```

Updated documents:

* `docs/api-spec.md`
* `docs/background-job-spec.md`
* `docs/contact-collection-design.md`
* `docs/internal-api-contracts.md`

## Files Modified

* `docs/api-spec.md`
* `docs/architecture.md`
* `docs/background-job-spec.md`
* `docs/contact-collection-design.md`
* `docs/data-acquisition-strategy-v1.md`
* `docs/data-model.md`
* `docs/dead-letter-strategy.md`
* `docs/implementation-roadmap.md`
* `docs/internal-api-contracts.md`
* `docs/job-queue-design.md`
* `docs/job-queue-spec.md`
* `docs/phase-4-design-readiness-report.md`
* `docs/rbac-permissions-matrix.md`

## Files Created

* `docs/phase-4-remediation-report.md`
* `docs/phase-4-implementation-readiness-report.md`

## Remaining Unresolved Conflicts

None identified in active Phase 4 implementation documentation.

Historical findings remain preserved in `docs/phase-4-final-readiness-review.md` for audit trail purposes.
