# Implementation Roadmap (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines the **exact build order** of the system.

It ensures:

* no random development order
* no missing dependencies
* no premature optimization
* no feature drift
* controlled MVP delivery

---

# 2. Development Philosophy

We follow:

### Vertical Slice Development

Each phase produces a **working system**, not isolated components.

---

### Incremental Delivery

Each phase must be:

* deployable
* testable
* usable

---

### Dependency-First Execution

Nothing is built before its dependency exists.

---

# 3. MVP Definition

The MVP must allow users to:

* search businesses by industry + location
* view results
* see basic contact info
* export leads

No advanced enrichment required in MVP.

---

# 4. Phase 0 — Project Bootstrap

## Goals

Initialize system foundation.

---

## Tasks

* Create monorepo structure
* Setup Docker Compose
* Setup PostgreSQL container
* Setup FastAPI backend skeleton
* Setup Next.js frontend skeleton
* Configure environment system
* Setup linting and formatting

---

## Output

Working empty system:

* frontend loads
* backend responds `/health`
* database connected

---

# 5. Phase 1 — Authentication System

## Goals

Secure user system.

---

## Backend

* JWT authentication
* HTTP-only secure cookies
* Opaque refresh token storage
* CSRF protection
* User model
* Password hashing (Argon2id)
* Login/register endpoints

---

## Frontend

* Login page
* Register page
* Auth context

---

## Output

Users can:

* register
* login
* access protected routes

---

# 6. Phase 2 — Core Database Models

## Goals

Create system data foundation.

---

## Models

* Users
* Businesses
* Contacts
* Search Logs (`search_logs`)
* Exports
* Refresh Tokens

---

## Output

* database schema operational
* migrations working
* ORM connected

---

# 7. Phase 3 — Lead Search Engine (Core Feature)

## Goals

Enable search functionality.

---

## Backend

* search API endpoint
* filter by:

  * industry
  * country
  * state
  * city

---

## Worker

* basic data retrieval engine
* search logging support

---

## Frontend

* search form UI
* results table UI

---

## Output

Users can search and see results.

---

# 8. Phase 4 — Data Acquisition Engine

## Goals

Build real data ingestion system.

---

## Components

* Phase 4A database migration for contact traceability and idempotency constraints
* web scraping module
* directory parser
* public website contact collection
* CSV export background processing
* PostgreSQL-backed job queue
* dead-letter handling
* internal worker APIs
* normalization pipeline

---

## Output

System can populate:

* business names
* addresses
* websites
* public contact information from public websites
* source traceability
* CSV export files

Phase 4 excludes decision-maker identification, LinkedIn people discovery, enrichment, and opportunity scoring.

---

# 9. Phase 5 - Frontend Dashboard Completion

## Goals

Complete user-facing dashboard workflows around the data already collected in MVP.

---

## Features

* improved search result views
* business detail UI
* contact/source display UI
* export status UI

---

## Output

Users can view collected businesses, contacts, sources, and export status in the dashboard.

---

# 10. Phase 6 - Reserved Post-MVP Contact Intelligence

## Goals

Reserved for future planning. This phase is not part of MVP implementation.

---

## Features

Not defined for MVP.

---

## Output

Not defined for MVP.

---

# 11. Phase 7 - Reserved Post-MVP Analysis

## Goals

Reserved for future planning. This phase is not part of MVP implementation.

---

## Inputs

Not defined for MVP.

---

## Output

Not defined for MVP.

---

# 12. Phase 8 - Post-MVP Export Enhancements

## Goals

Enhance export workflows after the MVP CSV export background job is operational.

---

## Features

* filtered export
* bulk selection
* additional output formats if approved

---

## Output

Users can use advanced export workflows beyond the Phase 4 MVP CSV export job.

---

# 13. Phase 9 — UI/UX Enhancement

## Goals

Improve usability.

---

## Features

* dashboard analytics
* filters refinement
* loading states
* error states
* dark mode polish

---

# 14. Phase 10 — Security Hardening

## Goals

Production-grade security.

---

## Tasks

* rate limiting
* request validation
* audit logs
* input sanitization
* dependency scanning
* container scanning

---

# 15. Phase 11 — Performance Optimization

## Goals

Scale readiness.

---

## Tasks

* caching layer (Redis future)
* query optimization
* pagination improvements
* async job optimization

---

# 16. Phase 12 — Testing & QA

## Goals

Stability assurance.

---

## Tests

* unit tests
* integration tests
* API tests
* frontend component tests

---

# 17. Phase 13 — Deployment Readiness

## Goals

Production deployment.

---

## Tasks

* Docker Compose finalization
* environment separation
* backup strategy activation
* logging validation

---

# 18. Phase 14 — Beta Release

## Goals

Real user testing.

---

## Features

* feedback logging
* usage tracking
* error monitoring

---

# 19. Phase 15 — Post-MVP Enhancements

Future upgrades:

* Redis queue system
* Kubernetes scaling
* multi-tenant architecture
* billing system
* CRM integration
* API monetization

---

# 20. Success Criteria

System is successful when:

✓ Users can search businesses
✓ Leads are returned accurately
✓ Public contact information is available where found
✓ Leads can be exported
✓ System is stable under load
✓ No critical security issues
✓ Deployment is reproducible

---

# 21. Execution Rule

No phase can be skipped.

Each phase must be:

* fully completed
* tested
* deployable
* documented

before moving to the next.

---

# 22. Final Principle

> “Build in layers. Each layer must work independently before adding complexity.”
