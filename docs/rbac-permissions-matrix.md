# RBAC Permissions Matrix

Project: Lead Generator App

Repository: lead-generator-app

## Purpose

This document defines V1 role-based access control permissions for public APIs under `/api/v1/*` and internal APIs under `/internal/v1/*`.

## V1 Roles

| Role | Description |
| --- | --- |
| `admin` | Administrative user with access to user-facing APIs, audit review, and controlled operational endpoints. |
| `user` | Standard authenticated user with access to MVP search, business detail, contact, source, and CSV export workflows. |
| `system_worker` | Internal worker identity resolved from a valid `INTERNAL_API_TOKEN`; not a browser user role. |

## Permission Naming

Permissions use the format:

```text
resource:action
```

Examples:

```text
auth:me
business:read
search:create
export:create
audit:read
internal:contact_collection
```

## Authentication Endpoint Permissions

| Endpoint | Method | Required Role | Required Permission | Access Rationale |
| --- | --- | --- | --- | --- |
| `/api/v1/auth/csrf` | `GET` | Public | `auth:csrf` | Allows clients to obtain a CSRF token before state-changing authentication requests. |
| `/api/v1/auth/register` | `POST` | Public | `auth:register` | Allows new users to create an account after request validation and CSRF validation. |
| `/api/v1/auth/login` | `POST` | Public | `auth:login` | Allows existing users to authenticate after request validation and CSRF validation. |
| `/api/v1/auth/refresh` | `POST` | Authenticated user or admin | `auth:refresh` | Allows an authenticated browser session to rotate tokens using the refresh token cookie. |
| `/api/v1/auth/logout` | `POST` | Authenticated user or admin | `auth:logout` | Allows the current session to revoke its refresh token and clear cookies. |
| `/api/v1/auth/logout-all` | `POST` | Authenticated user or admin | `auth:logout_all` | Allows the current account to revoke all active sessions. |
| `/api/v1/auth/me` | `GET` | Authenticated user or admin | `auth:me` | Allows the current authenticated account to read its own identity and role. |

## Search Endpoint Permissions

| Endpoint | Method | Required Role | Required Permission | Access Rationale |
| --- | --- | --- | --- | --- |
| `/api/v1/search` | `POST` | `user`, `admin` | `search:create` | Allows authenticated users to run MVP business searches by industry and location. |
| `/api/v1/search/history` | `GET` | `user`, `admin` | `search:history` | Allows authenticated users to review persisted search history from the MVP search log. |

## Business Endpoint Permissions

| Endpoint | Method | Required Role | Required Permission | Access Rationale |
| --- | --- | --- | --- | --- |
| `/api/v1/businesses/{id}` | `GET` | `user`, `admin` | `business:read` | Allows authenticated users to view business details returned by MVP search workflows. |
| `/api/v1/businesses/{id}/contacts` | `GET` | `user`, `admin` | `contact:read` | Allows authenticated users to view public contact information associated with a business. |
| `/api/v1/businesses/{id}/sources` | `GET` | `user`, `admin` | `source:read` | Allows authenticated users to inspect source attribution for business and contact records. |

## Export Endpoint Permissions

| Endpoint | Method | Required Role | Required Permission | Access Rationale |
| --- | --- | --- | --- | --- |
| `/api/v1/exports` | `POST` | `user`, `admin` | `export:create` | Allows authenticated users to generate CSV exports for permitted lead data. |

## Audit Endpoint Permissions

| Endpoint | Method | Required Role | Required Permission | Access Rationale |
| --- | --- | --- | --- | --- |
| `/api/v1/audit-logs` | `GET` | `admin` | `audit:read` | Allows administrators to review security and activity audit records for traceability. |
| `/api/v1/audit-logs/{id}` | `GET` | `admin` | `audit:read` | Allows administrators to inspect a specific audit event without exposing logs to standard users. |

## Internal Worker Endpoint Permissions

Internal endpoints must not be publicly exposed. They must be reachable only through approved backend or worker network paths and must require internal authentication in addition to RBAC permission checks.

Canonical internal security model:

* Authentication: `INTERNAL_API_TOKEN` in `X-Internal-API-Token`
* Identity: successful validation resolves to `system_worker`
* Authorization: worker-specific RBAC permissions

| Endpoint | Method | Required Role | Required Permission | Access Rationale |
| --- | --- | --- | --- | --- |
| `/internal/v1/contact-collection` | `POST` | `system_worker` | `internal:contact_collection` | Restricts contact collection worker execution to controlled internal access only. |
| `/internal/v1/csv-export` | `POST` | `system_worker` | `internal:csv_export` | Restricts CSV export worker execution to controlled internal access only. |
| `/internal/v1/jobs/{job_id}` | `GET` | `system_worker` | `internal:job_read` | Allows workers and controlled backend internals to inspect background job status without exposing job state publicly. |
| `/internal/v1/jobs/{job_id}/retry` | `POST` | `system_worker` | `internal:job_retry` | Restricts retry creation to authorized internal workflows after failure or dead-letter review. |
| `/internal/v1/jobs/{job_id}/cancel` | `POST` | `system_worker` | `internal:job_cancel` | Restricts cancellation of pending or running jobs to authorized internal workflows. |

## Role Permission Summary

| Role | V1 Permissions |
| --- | --- |
| `user` | `auth:refresh`, `auth:logout`, `auth:logout_all`, `auth:me`, `search:create`, `search:history`, `business:read`, `contact:read`, `source:read`, `export:create` |
| `admin` | All `user` permissions plus `audit:read` |
| `system_worker` | `internal:contact_collection`, `internal:csv_export`, `internal:job_read`, `internal:job_retry`, `internal:job_cancel` |

## Enforcement Rules

* Public authentication bootstrap endpoints do not require an existing authenticated role, but they must still enforce request validation, rate limiting, request tracing, sanitized errors, and CSRF validation where cookies are accepted.
* All authenticated public endpoints must validate identity, role, and permission before execution.
* State-changing endpoints must validate CSRF tokens.
* Permission denials must be audit logged.
* Internal endpoints must never be publicly exposed.
* Standard users must not access audit logs or internal worker endpoints.

## MVP Exclusions

The V1 MVP permission set does not include permissions for:

* decision-maker identification
* opportunity scoring
* AI enrichment
* website intelligence
* user administration APIs

These exclusions must not be implemented during Phase 4.
