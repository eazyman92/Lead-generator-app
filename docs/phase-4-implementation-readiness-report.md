# Phase 4 Implementation Readiness Report

Date: 2026-06-25

Project: Lead Generator App

Scope: Phase 4A documentation readiness after remediation. No application code was modified.

## Readiness Summary

The Phase 4 documentation now provides a consistent implementation contract for the data acquisition engine.

Phase 4A scope is limited to:

* public contact collection
* CSV export background processing
* PostgreSQL-backed background jobs
* internal worker APIs
* retry handling
* dead-letter handling
* idempotency enforcement
* source traceability
* audit logging

Explicitly excluded from Phase 4A:

* decision-maker identification
* LinkedIn people discovery
* enrichment
* opportunity scoring
* AI intelligence workflows

## Architecture Consistency

The architecture documentation now describes Phase 4 worker responsibilities as:

* public contact collection
* CSV export generation
* dead-letter handling
* source traceability

No future scoring or enrichment workflow is included in the active Phase 4 worker architecture.

## API Consistency

Public and internal API documents now align.

Internal APIs are documented in both `api-spec.md` and `internal-api-contracts.md`:

* `POST /internal/v1/contact-collection`
* `POST /internal/v1/csv-export`
* `GET /internal/v1/jobs/{job_id}`
* `POST /internal/v1/jobs/{job_id}/retry`
* `POST /internal/v1/jobs/{job_id}/cancel`

All internal APIs are marked as internal-only.

## Security Consistency

The canonical internal security model is consistent:

* Authentication: `INTERNAL_API_TOKEN`
* Identity: `system_worker`
* Authorization: worker-specific RBAC permissions
* Network: private Docker network only
* Tracing: `X-Request-ID`

RBAC permissions are documented for contact collection, CSV export, job read, job retry, and job cancellation.

## Database Consistency

The database model supports Phase 4A through existing tables:

* `businesses`
* `contacts`
* `data_sources`
* `exports`
* `background_jobs`
* `audit_logs`

Contact source traceability is canonical:

* `contacts.business_id`
* `contacts.source_id`
* `contacts.collection_timestamp`

## Job Lifecycle Consistency

The job lifecycle is documented with:

* pending jobs
* running jobs
* completed jobs
* failed jobs
* retry scheduling
* cancellation handling
* dead-letter handling

Dead-lettered jobs remain in `background_jobs` with:

```text
status = failed
payload.dead_letter = true
```

## Idempotency Consistency

Contact collection:

* unique job keys use `contact_collection:{business_id}:{source_hash_or_discovery_mode}`
* duplicate pending or running jobs return the existing job
* retries must be safe to resume without duplicate contacts

CSV export:

* one active `csv_export` job is allowed per export request
* job keys use `csv_export:{export_id}`
* duplicate pending or running jobs return the existing job

## Error Taxonomy Consistency

The job error taxonomy now includes:

```text
BUSINESS_NOT_FOUND
```

This error is documented for missing target businesses during contact collection.

## Remaining Blockers

None.

## Remaining Major Issues

None.

## Remaining Minor Issues

None.

## Final Verdict

READY FOR PHASE 4A IMPLEMENTATION
