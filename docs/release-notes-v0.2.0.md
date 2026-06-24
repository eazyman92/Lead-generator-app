# Release Notes v0.2.0

Project: Lead Generator App

Release scope: Completion summary through Phase 2.

## Overview

Version 0.2.0 documents the completed project foundation through authentication, authorization, and audit hardening. The repository now contains the core development scaffold, database foundation, V1 authentication system, RBAC documentation, and security audit improvements required before Phase 3 Search Engine work begins.

## Completed Phases

* Phase 0 Repository Bootstrap
* Phase 1 Database Foundation
* Phase 2 Authentication Foundation
* Phase 2 Audit Hardening
* RBAC Permissions Matrix

## Phase 0 Repository Bootstrap

Completed repository and development foundation:

* Frontend skeleton using Next.js, TypeScript, and TailwindCSS
* Backend skeleton using FastAPI
* Worker skeleton using Python
* Docker Compose service definitions
* Backend, frontend, and worker Dockerfiles
* Shared configuration folders
* Script and test structure
* Health check endpoints
* PostgreSQL container configured as an internal service only

## Phase 1 Database Foundation

Completed database foundation:

* SQLAlchemy models
* Alembic migration structure
* Initial core schema migration
* Repository layer
* Pydantic schemas
* Database test scaffolding
* Database ERD documentation

Current database tables:

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

## Phase 2 Authentication Foundation

Implemented V1 authentication endpoints:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
GET  /api/v1/auth/csrf
```

Completed authentication features:

* User registration
* User login
* User logout
* Logout all devices
* Current user lookup
* CSRF token endpoint
* JWT access tokens
* Opaque refresh tokens
* Refresh token rotation
* Refresh token reuse detection
* Argon2id password hashing
* HTTP-only access and refresh token cookies
* Standard API response wrappers
* Authentication audit events

## Phase 2 Audit Hardening

Completed audit hardening:

* CSRF validation failures are audit logged.
* RBAC permission denials are audit logged.
* Audit metadata avoids token, password, and secret values.
* Refresh-token identity lookup uses stored token hashes only.
* Existing authentication error behavior is preserved.

## RBAC Permissions Matrix

Added `docs/rbac-permissions-matrix.md` defining V1 permissions for:

* Authentication endpoints
* Search endpoints
* Business endpoints
* Export endpoints
* Internal worker endpoints
* Audit endpoints
* Future scope permissions

V1 roles:

* `admin`
* `user`

## Security State

Current security foundation includes:

* No hardcoded secrets required by application configuration
* Environment-variable based configuration
* PostgreSQL kept internal to the Docker network
* HTTP-only cookie authentication
* Refresh token hashing
* Refresh token rotation
* Refresh token reuse detection
* CSRF protection
* RBAC permission model
* Audit logging for authentication and security events

## Documentation Added or Updated

Important completed documentation includes:

* `docs/database-erd.md`
* `docs/authentication-implementation-design.md`
* `docs/phase-2-auth-implementation-report.md`
* `docs/phase-2-auth-validation-report.md`
* `docs/phase-2-auth-audit-hardening-report.md`
* `docs/rbac-permissions-matrix.md`
* `README.md`

## Not Included in v0.2.0

The following features remain planned and are not part of the completed Phase 2 implementation:

* Search engine implementation
* Business search API implementation
* Lead acquisition
* Contact collection workflows
* CSV export implementation
* Enrichment
* Opportunity scoring
* Frontend dashboard pages

## Next Milestone

Phase 3 Search Engine.

The next milestone should implement MVP business search while preserving the approved architecture, security standards, database foundation, and RBAC permissions model.
