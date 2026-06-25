# Search Implementation Design

Project: Lead Generator App

Repository: lead-generator-app

Status: Phase 3A design only.

## 1. Purpose

This document defines the V1 MVP search architecture for Lead Generator App.

The search domain must allow authenticated users to search existing business records by industry and location, return paginated results, persist search analytics, and write audit events.

This document does not implement code.

## 2. Scope

V1 search includes:

* Business search by industry and location
* Paginated search results
* Business detail lookup
* Public contact lookup for a business
* Source attribution lookup for a business
* Search logging through `search_logs`
* Audit logging through `audit_logs`
* RBAC enforcement
* Rate limiting requirements
* Standard response and error contracts

V1 search uses the existing database foundation and approved technology stack only.

## 3. Architecture Overview

Search follows the existing backend layering standard:

```text
Next.js frontend
  -> FastAPI /api/v1/search
  -> Search service
  -> BusinessRepository and SearchLogRepository
  -> PostgreSQL
  -> Standard API response
```

The backend must not perform raw SQL in route handlers. Routes validate input and delegate to services. Services coordinate repositories and audit logging. Repositories perform database access only.

## 4. Backend Module Responsibilities

### backend/app/api/

Planned API modules:

| Module | Responsibility |
| --- | --- |
| `search.py` | Expose `POST /api/v1/search`, validate request body, enforce auth, RBAC, CSRF, and return standard response. |
| `businesses.py` | Expose business detail, contacts, and sources read endpoints. |

### backend/app/services/

Planned service modules:

| Module | Responsibility |
| --- | --- |
| `search_service.py` | Normalize filters, run business search, write search log, write audit event, return paginated result data. |
| `business_service.py` | Load business detail, contacts, social profiles, and source attribution for read endpoints. |

### backend/app/repositories/

Repository responsibilities:

| Repository | Responsibility |
| --- | --- |
| `BusinessRepository` | Query businesses by industry, country, state, and city with deterministic sorting and pagination. |
| `SearchLogRepository` | Persist one `search_logs` row per accepted search request. |
| `AuditLogRepository` | Persist user activity and security-relevant search events. |
| `ContactRepository` | Return contacts for a business detail request. |
| `DataSourceRepository` | Return source attribution for a business detail request. |
| `SocialProfileRepository` | Return social profiles for a business detail request. |

### backend/app/schemas/

Planned schema responsibilities:

| Schema Area | Responsibility |
| --- | --- |
| Search request schema | Validate search filters and pagination. |
| Search response schema | Define business result summary and pagination metadata. |
| Business detail schema | Define business detail response payloads. |
| Pagination schema | Reuse a consistent pagination contract for list responses. |

## 5. Search Workflow

1. Client requests a CSRF token if needed.
2. Client sends `POST /api/v1/search` with filters and pagination.
3. API validates the access token cookie.
4. API enforces RBAC permission `search:create`.
5. API validates CSRF because search is a state-changing logged action.
6. API validates request body with Pydantic.
7. Search service normalizes filters.
8. Search service asks `BusinessRepository` for matching businesses and total count.
9. Search service writes one `search_logs` row with filters and `results_count`.
10. Search service writes one `audit_logs` row for the authenticated user.
11. API returns a standard success wrapper with results and pagination metadata.

## 6. Search Filters

V1 filters are intentionally small and aligned to existing indexed fields.

| Filter | Required | Type | Rule |
| --- | --- | --- | --- |
| `industry` | Yes | string | 2-100 characters after trimming. |
| `country` | Yes | string | 2-100 characters after trimming. |
| `state` | Yes | string | 1-100 characters after trimming. |
| `city` | Yes | string | 1-100 characters after trimming. |

Normalization rules:

* Trim leading and trailing whitespace.
* Collapse repeated internal whitespace.
* Preserve display casing in responses.
* Use case-insensitive matching for queries.
* Reject empty strings after trimming.
* Reject unknown fields in the request body.

## 7. Pagination Contract

All list responses in the search domain must use page-based pagination.

Request fields:

| Field | Default | Minimum | Maximum |
| --- | --- | --- | --- |
| `page` | `1` | `1` | No fixed maximum; must be bounded by integer validation. |
| `per_page` | `25` | `1` | `100` |

Offset calculation:

```text
offset = (page - 1) * per_page
```

Response pagination object:

```json
{
  "page": 1,
  "per_page": 25,
  "total": 100,
  "total_pages": 4,
  "has_next": true,
  "has_previous": false
}
```

Rules:

* `total` is the total number of records matching the filters before pagination.
* `total_pages` is `ceil(total / per_page)`.
* Empty result sets return an empty `results` array with `total` set to `0`.
* Requests beyond the last page return an empty `results` array, not an error.

## 8. Sorting

V1 search uses deterministic default sorting:

```text
name ASC, id ASC
```

The initial implementation should not expose arbitrary sort fields unless a later design updates this document.

## 9. Search Logging Behavior

Every accepted search request must create a `search_logs` row.

Existing table:

```text
search_logs
```

Fields to write:

| Field | Value |
| --- | --- |
| `user_id` | Authenticated user that submitted the search. |
| `request_id` | Request trace identifier. |
| `industry` | Normalized industry filter. |
| `country` | Normalized country filter. |
| `state` | Normalized state filter. |
| `city` | Normalized city filter. |
| `results_count` | Total matching result count before pagination. |
| `created_at` | Database timestamp. |

Search logs are analytics records and must be scoped to the authenticated user. Search history queries must filter by `search_logs.user_id`.

## 10. Audit Logging Behavior

Every successful search request must write an audit event.

Event type:

```text
business_search
```

Required audit fields:

| Field | Value |
| --- | --- |
| `user_id` | Authenticated user id. |
| `event_type` | `business_search`. |
| `ip_address` | Request IP address when available. |
| `request_id` | Current request id. |
| `metadata` | Safe search metadata. |
| `created_at` | Database timestamp. |

Safe metadata:

```json
{
  "industry": "gym",
  "country": "United States",
  "state": "Texas",
  "city": "Houston",
  "page": 1,
  "per_page": 25,
  "results_count": 42
}
```

Audit metadata must not include passwords, tokens, secrets, raw cookies, stack traces, or raw database errors.

Permission denials are handled by the existing RBAC denial audit behavior.

## 11. RBAC

Required permission:

```text
search:create
```

Allowed roles:

```text
user
admin
```

Search routes must validate:

* Authenticated identity
* Active user state
* Role
* Permission

## 12. Rate Limiting Requirements

Search must follow the project security standards:

| Limit | Scope |
| --- | --- |
| 60 requests per minute | Per authenticated user |
| 1000 requests per day | Per authenticated user |

Additional V1 search-specific requirements:

* Rate limit checks occur before database search execution.
* Rate limit errors return HTTP `429`.
* Rate limit errors use the standard error wrapper.
* Rate limit failures should be audit logged when an authenticated user is known.
* No new external rate limiting technology is introduced in Phase 3; the V1 implementation uses the approved in-process project pattern for the Docker Compose MVP foundation.

## 13. Error Handling

Search errors must use the standard error contract.

| Condition | HTTP Status | Error Code |
| --- | --- | --- |
| Missing or invalid access token | `401` | `AUTHENTICATION_REQUIRED` or `INVALID_ACCESS_TOKEN` |
| Missing permission | `403` | `PERMISSION_DENIED` |
| CSRF validation failure | `403` | `CSRF_VALIDATION_FAILED` |
| Invalid filters or pagination | `422` | `VALIDATION_ERROR` |
| Rate limit exceeded | `429` | `RATE_LIMIT_EXCEEDED` |
| Unexpected backend failure | `500` | `INTERNAL_SERVER_ERROR` |

Errors must not expose raw SQL, stack traces, secrets, tokens, file paths, or internal exception messages.

## 14. Query Behavior

V1 search queries:

* Use PostgreSQL through SQLAlchemy.
* Query only existing `businesses` records.
* Filter by `industry`, `country`, `state`, and `city`.
* Use indexed fields where available.
* Return only paginated results.
* Avoid unbounded list queries.
* Avoid raw SQL in route handlers.

## 15. Response Data Rules

Search result rows must include only safe business summary fields:

* `id`
* `name`
* `industry`
* `website`
* `phone`
* `email`
* `country`
* `state`
* `city`
* `address`
* `source_type`

Response payloads must not include internal audit metadata or database implementation details.

## 16. Test Strategy Summary

Phase 3 implementation should add tests for:

* Search request validation.
* Pagination calculations.
* Repository filtering.
* Search log creation.
* Audit log creation.
* RBAC enforcement.
* CSRF enforcement.
* Rate limit error behavior.
* Empty result sets.
* Standard response and error wrappers.

Detailed validation strategy is defined in `search-validation-strategy.md`.

## 17. Implementation Boundary

Phase 3 search implementation must not change the approved tech stack, authentication strategy, repository structure, API versioning, or database exposure rules.

Any database schema change must be documented and migrated through Alembic before implementation.
