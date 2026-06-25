# Data Acquisition Strategy V1

Project: Lead Generator App

Status: MVP documentation for Phase 4 Data Acquisition Engine.

## 1. Purpose

This document defines the approved MVP data acquisition strategy.

Phase 4 may collect publicly available business and contact information from allowed sources. Phase 4 must not implement decision-maker identification, opportunity scoring, AI enrichment, technology intelligence, or paid-data acquisition.

## 2. Approved MVP Scope

Included:

* Business discovery by industry and location.
* Website discovery for official public business websites.
* Public contact page discovery.
* Public contact extraction.
* Public email and phone extraction when explicitly published.
* Public social profile URL collection when explicitly linked or published by the business.
* Source traceability for collected data.
* Export generation as a background job.

Excluded:

* Decision-maker identification.
* Role-based lead prioritization.
* Opportunity scoring.
* AI enrichment.
* Website technology detection.
* Chatbot, booking, analytics, or CMS detection.
* LinkedIn scraping automation.
* Hidden email guessing.
* Paid datasets.
* Outreach automation.
* CRM workflows.

## 3. Core Principles

* Collect public business data only.
* Prefer official business websites and official contact pages.
* Store source URLs for traceability.
* Respect robots.txt where applicable.
* Stop collection when blocked.
* Avoid repeated failed requests.
* Use conservative request rates.
* Do not bypass access controls.
* Do not collect private or credentialed data.

## 4. Acquisition Workflow

### Stage 1: Business Discovery

Inputs:

* industry
* country
* state
* city
* request_id
* user_id when triggered by a user action

Outputs:

* business name
* website when available
* phone when publicly listed
* address
* industry
* country
* state
* city
* source attribution

### Stage 2: Website Discovery

The worker may identify official public websites from allowed public sources.

Allowed website discovery targets:

* official business website
* official contact page
* official about page
* official footer contact area

The worker must not authenticate into websites or bypass access restrictions.

### Stage 3: Public Contact Extraction

The worker may collect public contact data only when explicitly published.

Allowed contact fields:

* full_name when explicitly listed
* role when explicitly listed
* public business email
* public business phone
* source_url

Generic business contacts are allowed:

* info@
* contact@
* sales@
* support@
* hello@

Named contacts are allowed only when the contact information is explicitly published as business contact information. The worker must not infer decision-maker status.

### Stage 4: Social Profile URL Collection

The worker may store public social profile URLs when explicitly linked from an allowed source.

Allowed platforms:

* Facebook
* Instagram
* LinkedIn company profile
* YouTube

The worker must not scrape LinkedIn for emails or private profile data.

### Stage 5: Source Attribution

Every collected business, contact, and social profile update must be traceable to a source.

Source records use:

* source_type
* source_url
* trust_tier
* confidence_score
* collected_at

Contact records must store `business_id`, `source_id`, `source_url`, and `collection_timestamp`. Contact source type, trust tier, and confidence score are represented by `contacts.source_id -> data_sources.id`.

## 5. Allowed Sources

Allowed sources:

* official business websites
* public contact pages
* public about pages
* public business directories
* government business registries
* verified business registries
* public social profiles where contact information is explicitly shown

## 6. Prohibited Sources And Methods

Prohibited:

* private data
* credentialed scraping
* bypassing access controls
* hidden email guessing
* LinkedIn scraping automation
* paid datasets
* data from pages that explicitly prohibit automated collection
* repeated requests after a block or denial

## 7. Source Trust Ranking

Trust tiers:

| Tier | Source type | Confidence range |
| --- | --- | --- |
| A | Official business website, contact page, about page | 90-100 |
| B | Government registry, verified registry, press release | 75-90 |
| C | Public industry directory or business listing | 50-75 |
| D | Unverified public third-party listing | 0-50 |

Confidence scores must describe source reliability only. They must not be used for opportunity scoring or lead prioritization in Phase 4.

## 8. Data Quality Rules

Workers must:

* normalize URLs
* normalize phone numbers where possible
* trim and normalize whitespace
* avoid duplicate businesses
* avoid duplicate contacts for the same business and source
* preserve source URLs
* record failed-source reasons without storing secrets or raw page content

## 9. Job Usage

Phase 4 acquisition runs through PostgreSQL-backed background jobs using the existing `background_jobs` table.

Approved Phase 4 acquisition job type:

```text
contact_collection
```

Allowed supporting job type:

```text
csv_export
```

The `csv_export` job is part of the MVP background job system. One export request creates one active export job.

## 10. Audit Logging

Workers must log the canonical background job lifecycle events for job state changes:

* `background_job_created`
* `background_job_started`
* `background_job_completed`
* `background_job_failed`
* `background_job_retry_scheduled`
* `background_job_dead_lettered`

Workers must log contact collection domain events for collection-specific activity:

* `contact_collection_started`
* `contact_collection_completed`
* `contact_collection_failed`
* `source_skipped`
* `robots_denied`
* `contact_collected`
* `data_source_recorded`

Audit metadata must not include passwords, tokens, secrets, raw cookies, raw HTML, or raw database errors.

## 11. Success Criteria

Phase 4 design is successful when:

* Public contact collection can be implemented without ambiguity.
* Job lifecycle and retries are fully specified.
* Dead-letter handling is fully specified.
* Internal API contracts are fully specified.
* Compliance rules are enforceable.
* Source traceability is documented for contacts and businesses.
* No decision-maker identification, opportunity scoring, or AI enrichment is included.
