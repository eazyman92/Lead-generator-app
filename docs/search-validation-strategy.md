# Search Validation Strategy

Project: Lead Generator App

Repository: lead-generator-app

Status: Phase 3A design only.

## 1. Purpose

This document defines the V1 MVP validation and test strategy for the search domain.

It covers request validation, repository behavior, search logging, audit logging, RBAC, rate limiting, response contracts, and error handling.

This document does not implement code.

## 2. Validation Goals

Phase 3 search is ready only when:

* Search filters are validated with Pydantic.
* Pagination is bounded and deterministic.
* Repository queries return correct records.
* Search results use the standard response wrapper.
* Errors use the standard error wrapper.
* Search requests create `search_logs` rows.
* Search requests create safe `audit_logs` rows.
* RBAC permission checks are enforced.
* CSRF is enforced for `POST /api/v1/search`.
* Rate limit behavior is tested.
* Empty result sets are handled cleanly.

## 3. Request Validation Rules

### Search Filters

| Field | Valid Case | Invalid Cases |
| --- | --- | --- |
| `industry` | Non-empty string, 2-100 chars after trimming. | Missing, empty, whitespace-only, too short, too long, wrong type. |
| `country` | Non-empty string, 2-100 chars after trimming. | Missing, empty, whitespace-only, too short, too long, wrong type. |
| `state` | Non-empty string, 1-100 chars after trimming. | Missing, empty, whitespace-only, too long, wrong type. |
| `city` | Non-empty string, 1-100 chars after trimming. | Missing, empty, whitespace-only, too long, wrong type. |

### Pagination

| Field | Valid Case | Invalid Cases |
| --- | --- | --- |
| `page` | Integer greater than or equal to `1`. | `0`, negative number, float, string, null. |
| `per_page` | Integer from `1` through `100`. | `0`, negative number, value greater than `100`, float, string, null. |

### Unknown Fields

Unknown request fields must be rejected.

Expected error:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed."
  },
  "request_id": "..."
}
```

## 4. Response Contract Validation

Every successful search-domain response must include:

* `success`
* `data`
* `message`
* `request_id`

Every error response must include:

* `success`
* `error.code`
* `error.message`
* `request_id`

Paginated responses must include:

* `page`
* `per_page`
* `total`
* `total_pages`
* `has_next`
* `has_previous`

## 5. Repository Test Strategy

### BusinessRepository

Required tests:

* Filters by `industry`, `country`, `state`, and `city`.
* Matching is case-insensitive.
* Results are sorted by `name ASC, id ASC`.
* Pagination applies correct limit and offset.
* Total count returns all matches before pagination.
* Empty search returns no records and total `0`.
* Query does not return records outside the requested location.

### SearchLogRepository

Required tests:

* Creates a search log after an accepted search.
* Persists authenticated `user_id`.
* Persists `request_id`.
* Persists normalized filter values.
* Persists `results_count`.
* Does not require `user_id` or `request_id` because the existing table does not contain those fields.

### AuditLogRepository

Required tests:

* Creates `business_search` audit events.
* Persists `user_id`.
* Persists `request_id`.
* Persists IP address when available.
* Persists safe metadata.
* Does not persist tokens, cookies, passwords, secrets, or raw exception text.

## 6. Service Test Strategy

Search service tests should use repository fakes or a test database.

Required tests:

* Valid filters call the repository with normalized values.
* Search returns results and pagination metadata.
* Search writes one `search_logs` row per accepted search.
* Search writes one `business_search` audit event per successful search.
* Empty results still write search and audit logs.
* Repository errors are translated into sanitized application errors.
* Invalid pagination is rejected before repository calls.

Business service tests:

* Returns business detail for an existing business.
* Raises `BUSINESS_NOT_FOUND` for a missing business.
* Returns contacts with pagination.
* Returns sources with pagination.
* Does not expose internal database implementation details.

## 7. API Test Strategy

Use FastAPI test client or containerized integration tests with the project runtime.

### POST /api/v1/search

Required tests:

* Authenticated user can search with valid CSRF token.
* Authenticated admin can search with valid CSRF token.
* Missing access token returns `401`.
* Invalid access token returns `401`.
* Missing permission returns `403`.
* Missing CSRF token returns `403`.
* Invalid CSRF token returns `403`.
* Invalid filter values return `422`.
* Invalid pagination values return `422`.
* Rate limit exceeded returns `429`.
* Empty result set returns `200` with an empty `results` array.
* Successful response includes standard wrapper and pagination.

### GET /api/v1/businesses/{id}

Required tests:

* Authenticated user can read an existing business.
* Authenticated admin can read an existing business.
* Missing business returns `404`.
* Invalid UUID returns `422`.
* Missing permission returns `403`.
* CSRF is not required for GET.

### GET /api/v1/businesses/{id}/contacts

Required tests:

* Authenticated user can read contacts for an existing business.
* Missing business returns `404`.
* Pagination is enforced.
* Empty contacts return an empty array.
* Invalid pagination returns `422`.

### GET /api/v1/businesses/{id}/sources

Required tests:

* Authenticated user can read sources for an existing business.
* Missing business returns `404`.
* Pagination is enforced.
* Empty sources return an empty array.
* Invalid pagination returns `422`.

## 8. RBAC Validation

Required permissions:

| Endpoint | Permission |
| --- | --- |
| `POST /api/v1/search` | `search:create` |
| `GET /api/v1/businesses/{id}` | `business:read` |
| `GET /api/v1/businesses/{id}/contacts` | `contact:read` |
| `GET /api/v1/businesses/{id}/sources` | `source:read` |

Tests must verify:

* `user` role is allowed.
* `admin` role is allowed.
* Missing permission is denied.
* Denials are audit logged by existing RBAC denial behavior.

## 9. CSRF Validation

CSRF required:

```text
POST /api/v1/search
```

CSRF not required:

```text
GET /api/v1/businesses/{id}
GET /api/v1/businesses/{id}/contacts
GET /api/v1/businesses/{id}/sources
```

Tests must verify:

* Missing CSRF token rejects state-changing search requests.
* Mismatched CSRF token rejects state-changing search requests.
* Valid CSRF token allows state-changing search requests.
* CSRF failures are audit logged by existing CSRF failure behavior.

## 10. Rate Limiting Validation

Required project limits:

```text
60 requests/minute per user
1000 requests/day per user
```

Tests must verify:

* Requests under the limit proceed.
* Requests over the limit return HTTP `429`.
* Rate limit errors use the standard error wrapper.
* Rate limit checks run before database search execution.
* Authenticated rate limit denials are audit logged when possible.

## 11. Search Logging Validation

Test that one accepted search creates exactly one `search_logs` row.

Expected persisted fields:

```json
{
  "user_id": "uuid",
  "request_id": "...",
  "industry": "gym",
  "country": "United States",
  "state": "Texas",
  "city": "Houston",
  "results_count": 42
}
```

Search log tests must also verify:

* Invalid requests do not create search logs.
* Authentication failures do not create search logs.
* Permission denials do not create search logs.
* CSRF failures do not create search logs.

## 12. Audit Logging Validation

Test that successful searches create audit events.

Expected audit event:

```text
business_search
```

Required fields:

* `user_id`
* `event_type`
* `ip_address`
* `request_id`
* `metadata`
* `created_at`

Metadata must include:

* `industry`
* `country`
* `state`
* `city`
* `page`
* `per_page`
* `results_count`

Metadata must not include:

* Passwords
* Tokens
* Cookies
* Secrets
* Raw database errors
* Stack traces

## 13. Error Handling Validation

| Scenario | Expected Status | Expected Code |
| --- | --- | --- |
| Missing authentication | `401` | `AUTHENTICATION_REQUIRED` |
| Invalid access token | `401` | `INVALID_ACCESS_TOKEN` |
| Missing permission | `403` | `PERMISSION_DENIED` |
| CSRF validation failure | `403` | `CSRF_VALIDATION_FAILED` |
| Invalid body or query params | `422` | `VALIDATION_ERROR` |
| Missing business | `404` | `BUSINESS_NOT_FOUND` |
| Rate limit exceeded | `429` | `RATE_LIMIT_EXCEEDED` |
| Unexpected failure | `500` | `INTERNAL_SERVER_ERROR` |

Every error response must include `request_id`.

## 14. Database Integration Validation

Containerized PostgreSQL-backed tests should verify:

* Alembic migration is applied.
* Existing tables are available.
* Seeded businesses can be searched.
* Search logs are persisted.
* Audit logs are persisted.
* Pagination returns deterministic records.
* Repository methods use SQLAlchemy and do not bypass the repository pattern.

## 15. Performance Validation

V1 performance checks:

* Search endpoint returns within the documented UI target for typical result sets.
* Queries use indexed fields where available.
* `per_page` cannot exceed `100`.
* No unbounded business list is returned.
* Search count query and page query are measured in integration tests when feasible.

## 16. Documentation Validation

Before Phase 3 implementation is considered complete, verify that:

* `api-spec.md` reflects the final implemented search contract.
* `rbac-permissions-matrix.md` includes all search-domain permissions.
* `database-erd.md` remains accurate if migrations change.
* `README.md` status is updated after Phase 3 is completed.
* Any validation report records tests executed and known limitations.

## 17. Phase 3A Readiness Checklist

Phase 3 implementation can begin when:

* `search-implementation-design.md` exists.
* `business-search-api-design.md` exists.
* `search-validation-strategy.md` exists.
* V1 scope is limited to MVP search and business read workflows.
* API versioning is `/api/v1/*`.
* Response wrappers and error wrappers are documented.
* RBAC permissions are mapped.
* Search logging and audit logging behavior are defined.
* Rate limiting expectations are defined.
* Test strategy is defined.
