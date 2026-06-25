# Phase 4 Design Readiness Report

Date: 2026-06-25

Project: Lead Generator App

Scope: Documentation design pass only.

No application code was modified.

## Executive Summary

Phase 4 is ready for implementation from a documentation-design perspective.

The missing worker, queue, internal API, contact collection, and dead-letter documents have been created. Existing MVP documentation was updated to remove Phase 4 ambiguity around decision-maker identification, opportunity scoring, AI enrichment, and website intelligence.

Phase 4 implementation must remain limited to:

* public contact collection
* CSV export background processing
* public business/source traceability
* PostgreSQL-backed background jobs
* internal worker APIs
* compliance enforcement
* audit logging

## Documents Created

* `docs/job-queue-design.md`
* `docs/background-job-spec.md`
* `docs/internal-api-contracts.md`
* `docs/contact-collection-design.md`
* `docs/dead-letter-strategy.md`
* `docs/phase-4-design-readiness-report.md`

## Existing Documents Updated

* `docs/data-acquisition-strategy-v1.md`
* `docs/job-queue-spec.md`
* `docs/api-spec.md`
* `docs/data-model.md`
* `docs/project-structure.md`
* `docs/compliance-policy.md`
* `docs/rbac-permissions-matrix.md`
* `docs/architecture.md`
* `docs/tech-stack.md`
* `docs/implementation-roadmap.md`

## Critical Findings

None.

## Major Findings

None.

## Minor Findings

None.

## Recommendations

### Recommendation 1: Keep Phase 4 Code Strictly Scoped

Implementation should follow the new design documents and avoid any feature outside public contact collection and approved background job behavior.

### Recommendation 2: Add `.env.example` Values During Implementation

Worker environment variables are now documented. The implementation phase should update `.env.example` only when wiring the actual worker configuration.

### Recommendation 3: Add Tests For Every Queue State Transition

Phase 4 implementation should include tests for claim, completion, retry, failure, dead-letter, stale lock recovery, and internal API validation.

## Design Coverage Matrix

| Area | Status | Source |
| --- | --- | --- |
| Worker architecture | Ready | `job-queue-design.md` |
| Job lifecycle | Ready | `background-job-spec.md` |
| Job states | Ready | `job-queue-design.md`, `background-job-spec.md` |
| Retry strategy | Ready | `job-queue-design.md`, `background-job-spec.md` |
| Failure handling | Ready | `background-job-spec.md` |
| Dead-letter strategy | Ready | `dead-letter-strategy.md` |
| Acquisition workflows | Ready | `data-acquisition-strategy-v1.md`, `contact-collection-design.md` |
| Public data source rules | Ready | `compliance-policy.md`, `contact-collection-design.md` |
| Compliance requirements | Ready | `compliance-policy.md`, `data-acquisition-strategy-v1.md` |
| Database support | Ready | `data-model.md`, `background-job-spec.md` |
| Audit logging requirements | Ready | `job-queue-design.md`, `contact-collection-design.md`, `dead-letter-strategy.md` |
| Internal API requirements | Ready | `internal-api-contracts.md` |
| Security requirements | Ready | `security-standards.md`, `internal-api-contracts.md` |
| Configuration requirements | Ready | `job-queue-design.md`, `project-structure.md` |
| Environment variables | Ready | `job-queue-design.md`, `project-structure.md` |

## MVP Scope Confirmation

Included in Phase 4:

* `contact_collection` background job design
* `csv_export` background job contract
* public contact extraction design
* source traceability design
* internal contact collection API contract
* job retry and dead-letter design
* worker security and configuration requirements

Explicitly excluded from Phase 4:

* decision-maker identification
* opportunity scoring
* AI enrichment
* website intelligence
* technology detection
* outreach automation
* paid data acquisition
* LinkedIn scraping automation

## Architecture Decisions

### Queue Backend

Use the existing PostgreSQL `background_jobs` table.

No external queue infrastructure is introduced.

### Dead-Letter Handling

Use the existing `background_jobs` table:

```text
status = failed
payload.dead_letter = true
```

No new dead-letter table is introduced.

### Retry Scheduling

Use:

```text
payload.retry_after
```

No schema change is required for Phase 4 design readiness.

### Contact Source Traceability

Contacts store:

```text
contacts.business_id
contacts.source_id
contacts.collection_timestamp
```

Source type, trust tier, and confidence score are traced through `contacts.source_id -> data_sources.id`. `contacts.source_url` remains a readable attribution field.

### Worker Authentication

Internal APIs require:

```text
X-Internal-API-Token
X-Request-ID
```

The token comes from:

```text
INTERNAL_API_TOKEN
```

## Implementation Readiness Assessment

Phase 4 can proceed to implementation.

The documentation now defines:

* queue architecture
* worker responsibilities
* job lifecycle states
* payload envelopes
* retry rules
* failure handling
* dead-letter handling
* internal API contracts
* contact collection workflow
* source traceability
* compliance rules
* security requirements
* environment variables

Implementation must not start Phase 5 or any future intelligence/scoring/enrichment functionality.
