# Contact Collection Design

Project: Lead Generator App

Status: Phase 4 MVP design.

## 1. Purpose

This document defines the approved MVP public contact collection workflow.

Public contact collection may collect explicitly published business contact information. It must not identify decision makers, rank leads, score opportunities, or perform AI enrichment.

## 2. Inputs

Contact collection jobs use:

* `business_id`
* optional `source_urls`
* `discovery_mode`
* `max_pages`
* `request_id`
* `created_by_user_id` when applicable

## 3. Allowed Collection Targets

Allowed targets:

* official business website
* official contact page
* official about page
* official footer contact area
* public business directory page
* government or verified business registry page
* public social page only when contact information is explicitly shown

Prohibited:

* pages requiring login
* pages that block automated access
* pages disallowed by robots.txt
* LinkedIn scraping automation
* private personal data
* paid datasets
* hidden email guessing

## 4. Workflow

### Step 1: Load Business

Worker loads the target business by `business_id`.

If the business does not exist:

* mark job as failed
* set `payload.dead_letter = true`
* use error code `BUSINESS_NOT_FOUND`
* write audit event

### Step 2: Resolve Source URLs

Worker determines source URLs from:

* explicit job `source_urls`
* existing business website
* already recorded data sources

Workers must not exceed `max_pages`.

### Step 3: Compliance Check

Before fetching a source, worker verifies:

* source scheme is HTTP or HTTPS
* source is not on a denylist
* source does not require authentication
* robots.txt allows collection where applicable
* domain rate limit permits request

### Step 4: Fetch Public Source

Worker fetches only allowed public pages.

Rules:

* use configured user agent
* apply request timeout
* follow only safe redirects
* reject unsupported content types
* do not store raw HTML in the database

### Step 5: Extract Public Contacts

Allowed extracted fields:

* full_name when explicitly published
* role when explicitly published
* email when explicitly published
* phone when explicitly published
* source_id
* source_url
* collection_timestamp

The worker must not infer:

* decision-maker status
* seniority ranking
* buying intent
* opportunity value

For existing `contacts.is_decision_maker`, Phase 4 must write `false`.

For existing `contacts.priority_score`, Phase 4 must write `0`.

### Step 6: Persist Source Traceability

For every source used, create or reuse a `data_sources` row with:

* `business_id`
* `source_type`
* `source_url`
* `trust_tier`
* `confidence_score`
* `collected_at`

For every contact, set:

* `contacts.business_id`
* `contacts.source_id`
* `contacts.source_url`
* `contacts.collection_timestamp`

Contact source type, trust tier, and confidence score are traced through `contacts.source_id -> data_sources.id`.

### Step 6.1: Protect Contact Fields At Rest

Phase 4A contact persistence must protect stored public contact values according to `security-standards.md`.

Ownership:

* `backend/app/services/` validates and normalizes collected contact values.
* `backend/app/repositories/` owns encryption before insert/update and decryption when returning contact values to authorized API/service callers.
* Encryption configuration comes from `ENCRYPTION_KEY`.
* Raw contact email and phone values must not be written to logs, audit metadata, job payloads, or error messages.
* The worker may pass normalized contact values to the backend/repository boundary but must not bypass repository persistence rules.

Fields requiring at-rest protection:

* `contacts.email`
* `contacts.phone`

Readable source attribution fields such as `source_url`, `source_id`, and `collection_timestamp` remain unencrypted so traceability and compliance review remain queryable.

### Step 7: Deduplicate

Deduplicate contacts by:

* business_id
* source_id when source-specific uniqueness is required
* email when present
* phone when email is absent
* full_name plus source_url when email and phone are absent

Database enforcement:

* `data_sources` must enforce unique `(business_id, source_url)`.
* `contacts` must enforce the partial unique indexes documented in `data-model.md`.
* The worker must handle duplicate-key conflicts by reusing the existing row or treating the write as already completed.

### Step 7.1: Enforce Idempotency

Contact collection jobs must use unique job keys:

```text
contact_collection:{business_id}:{source_hash_or_discovery_mode}
```

If a pending or running job already exists for the same key, the system must return the existing job instead of creating a duplicate.

Processing must be retry-safe:

* repeated attempts must not create duplicate contacts
* repeated attempts must reuse existing `data_sources` rows when the source already exists
* partial previous attempts must be safe to continue
* all contacts written during retry must preserve `business_id`, `source_id`, and `collection_timestamp`

### Step 8: Audit

Required background job lifecycle events are defined in `job-queue-design.md` and must use `background_job_*` names.

Required contact collection domain audit events:

* `contact_collection_started`
* `source_checked`
* `source_skipped`
* `robots_denied`
* `contact_collected`
* `data_source_recorded`
* `contact_collection_completed`
* `contact_collection_failed`

## 5. Trust Tier Mapping

| Source | source_type | trust_tier | confidence_score |
| --- | --- | --- | --- |
| Official website contact page | `website` | A | 95 |
| Official website about page | `website` | A | 90 |
| Government registry | `directory` | B | 85 |
| Verified business registry | `directory` | B | 80 |
| Public industry directory | `directory` | C | 65 |
| Unverified public listing | `directory` | D | 40 |

Confidence scores describe source reliability only. They must not be used for opportunity scoring.

## 6. Error Handling

Retryable errors:

* network timeout
* DNS failure
* HTTP 429
* HTTP 5xx

Non-retryable errors:

* business not found (`BUSINESS_NOT_FOUND`)
* robots.txt denial
* source explicitly blocks automation
* source requires authentication (`SOURCE_AUTH_REQUIRED`)
* source forbids access (`SOURCE_FORBIDDEN`)
* prohibited source
* unsupported content type
* invalid payload

## 7. Security Requirements

Workers must:

* use least privilege
* run inside the private Docker network
* read configuration from environment variables
* never log raw contact payloads unnecessarily
* never log secrets
* never store raw page content
* include `request_id` in logs and audit events

## 8. MVP Exclusions

Phase 4 contact collection must not implement:

* decision-maker identification
* contact ranking
* opportunity scoring
* AI enrichment
* website technology detection
* chatbot detection
* booking-system detection
* email guessing
* outreach automation
