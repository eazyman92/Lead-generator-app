# Lead Generator App

Lead Generator App is a full-stack platform for discovering businesses, viewing business details, reading publicly available contact/source information, and preparing MVP lead workflows.

The project is built in phased milestones. The current implementation includes repository bootstrap, database foundation, authentication and authorization, audit hardening, and the Phase 3 Search Domain.

## Current Status

* Phase 0 Repository Bootstrap: Complete
* Phase 1 Database Foundation: Complete
* Phase 2 Authentication & Security: Complete
* Phase 3 Search Engine: Complete
* Phase 4 Data Acquisition Engine: Next milestone
* Phase 5 Export System: Planned
* Phase 6 Frontend Dashboard: Planned

## Release v0.3.0 Summary

Release v0.3.0 completes Phase 3 Search Engine work.

Completed in this release:

* V1 business search endpoint
* User-scoped search history
* Business detail endpoint with related data counts
* Paginated business contacts endpoint
* Paginated business sources endpoint
* Search-domain RBAC enforcement
* Search-domain audit logging
* Search-domain rate limiting
* Search log traceability with `user_id` and `request_id`
* API and documentation alignment after Phase 3 remediation

Out of scope for v0.3.0:

* Data acquisition engine
* Crawlers
* Enrichment
* Opportunity scoring
* CSV export implementation
* Frontend business pages

## Tech Stack

### Frontend

* Next.js
* TypeScript
* TailwindCSS

### Backend

* FastAPI
* SQLAlchemy 2.x
* Alembic
* Pydantic

### Database

* PostgreSQL 15.5

### Infrastructure

* Docker
* Docker Compose

## Repository Structure

```text
lead-generator-app/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   `-- services/
|   |-- tests/
|   |-- Dockerfile
|   `-- requirements.txt
|-- config/
|-- database/
|   |-- backups/
|   |-- migrations/
|   |   `-- versions/
|   |-- schemas/
|   `-- seeds/
|-- docker/
|-- docs/
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   `-- styles/
|   |-- Dockerfile
|   |-- package.json
|   |-- tailwind.config.ts
|   `-- tsconfig.json
|-- logs/
|-- scripts/
|-- tests/
|-- uploads/
|-- worker/
|   |-- config/
|   |-- tests/
|   |-- Dockerfile
|   |-- main.py
|   `-- requirements.txt
|-- .env.example
|-- alembic.ini
|-- docker-compose.yml
|-- pyproject.toml
`-- README.md
```

## Current API Endpoints

### Health

```text
GET /health
```

### Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
GET  /api/v1/auth/csrf
```

### Search

```text
POST /api/v1/search
GET  /api/v1/search/history
```

### Businesses

```text
GET /api/v1/businesses/{id}
GET /api/v1/businesses/{id}/contacts
GET /api/v1/businesses/{id}/sources
```

All V1 API responses use the standard response wrapper with `success`, `data`, `message`, and `request_id`. Error responses use the project error contract with `success`, `error.code`, `error.message`, and `request_id`.

## Current Database Entities

The current database foundation includes:

* `users`
* `refresh_tokens`
* `businesses`
* `contacts`
* `social_profiles`
* `data_sources`
* `search_logs`
* `exports`
* `background_jobs`
* `audit_logs`

Phase 3 remediation added user-scoped search history fields:

* `search_logs.user_id`
* `search_logs.request_id`

Database migrations are located under:

```text
database/migrations/versions/
```

## Current Security Controls

Implemented controls include:

* JWT access tokens
* Opaque refresh tokens
* Refresh token hashing
* Refresh token rotation
* Refresh token reuse detection
* Argon2id password hashing
* HTTP-only authentication cookies
* Secure cookie flag controlled by environment
* SameSite cookie configuration
* CSRF protection
* RBAC permissions
* Permission-denial audit logging
* CSRF-failure audit logging
* Authentication event audit logging
* Search-domain audit logging
* Request tracing with `request_id`
* Standard sanitized error responses
* No localStorage or sessionStorage token storage
* No hardcoded secrets
* PostgreSQL kept internal to the Docker network
* Search-domain rate limiting: `60 requests/minute` and `1000 requests/day` per user

## Docker Validation Status

Current confirmed Docker status:

* Docker Compose builds successfully.
* Containers have been validated healthy for the Phase 0 foundation.
* PostgreSQL network isolation has been verified.
* PostgreSQL is not publicly exposed.
* Backend exposure remains development-only.

Phase 3 validation status:

* Python compile validation passed for backend app and tests.
* Search schema tests passed in the host environment.
* Full FastAPI and SQLAlchemy-backed tests should be run inside the backend container or a Python 3.12 environment with `backend/requirements.txt` installed.
* The Phase 3 search-log migration should be applied and verified against PostgreSQL in Docker Compose.

## Running Locally

Create a local environment file:

```bash
cp .env.example .env
```

Fill in local placeholder values in `.env`, then build and start the stack:

```bash
docker compose up -d --build
```

Apply database migrations from the repository root:

```bash
alembic upgrade head
```

Check service status:

```bash
docker compose ps
```

Backend health:

```text
http://localhost:8000/health
```

Frontend:

```text
http://localhost:3000
```

Stop the local stack:

```bash
docker compose down
```

## Environment Variables

Environment variables are documented in:

```text
.env.example
```

Do not commit local `.env` files or real secret values.

## Documentation

Important documentation files:

* `docs/architecture.md`
* `docs/tech-stack.md`
* `docs/project-structure.md`
* `docs/security-standards.md`
* `docs/api-spec.md`
* `docs/api-error-contract.md`
* `docs/data-model.md`
* `docs/database-erd.md`
* `docs/authentication-spec.md`
* `docs/authentication-implementation-design.md`
* `docs/refresh-token-spec.md`
* `docs/csrf-protection-spec.md`
* `docs/rbac-permissions-matrix.md`
* `docs/search-implementation-design.md`
* `docs/business-search-api-design.md`
* `docs/search-validation-strategy.md`
* `docs/phase-1-validation-report.md`
* `docs/phase-2-auth-implementation-report.md`
* `docs/phase-2-auth-validation-report.md`
* `docs/phase-2-auth-audit-hardening-report.md`
* `docs/phase-3-search-implementation-report.md`
* `docs/phase-3-validation-report.md`
* `docs/phase-3-remediation-report.md`
* `docs/phase-3-final-validation-report.md`

## Next Milestone

Phase 4 Data Acquisition Engine.

Phase 4 should focus on collecting permitted public business and contact data using the approved architecture and compliance policy. It must preserve the existing authentication, RBAC, database, audit logging, request tracing, and Docker network security standards.
