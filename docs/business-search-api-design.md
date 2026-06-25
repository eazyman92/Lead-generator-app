# Business Search API Design

Project: Lead Generator App

Repository: lead-generator-app

Status: Phase 3A design only.

## 1. Purpose

This document defines the V1 MVP API contract for business search and related business read endpoints.

All endpoints must follow:

* Public API versioning: `/api/v1/*`
* Standard success response wrapper
* Standard error response wrapper
* JWT cookie authentication
* CSRF validation for state-changing requests
* RBAC permissions
* Request id tracing
* Audit logging
* Rate limiting

## 2. Endpoint Summary

| Endpoint | Method | Required Role | Required Permission | Purpose |
| --- | --- | --- | --- | --- |
| `/api/v1/search` | `POST` | `user`, `admin` | `search:create` | Search businesses by industry and location. |
| `/api/v1/search/history` | `GET` | `user`, `admin` | `search:history` | Read paginated MVP search history. |
| `/api/v1/businesses/{id}` | `GET` | `user`, `admin` | `business:read` | Read one business with related summary data. |
| `/api/v1/businesses/{id}/contacts` | `GET` | `user`, `admin` | `contact:read` | Read public contacts for one business. |
| `/api/v1/businesses/{id}/sources` | `GET` | `user`, `admin` | `source:read` | Read source attribution for one business. |

## 3. Standard Response Wrapper

Success responses:

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description"
  },
  "request_id": "..."
}
```

## 4. Pagination Contract

Paginated responses must include:

```json
{
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 42,
    "total_pages": 2,
    "has_next": true,
    "has_previous": false
  }
}
```

Pagination request values:

| Field | Default | Min | Max |
| --- | --- | --- | --- |
| `page` | `1` | `1` | Integer validation bound |
| `per_page` | `25` | `1` | `100` |

## 5. Search Businesses

Endpoint:

```text
POST /api/v1/search
```

Authentication:

```text
Required
```

Permission:

```text
search:create
```

CSRF:

```text
Required
```

### Request Body

```json
{
  "filters": {
    "industry": "gym",
    "country": "United States",
    "state": "Texas",
    "city": "Houston"
  },
  "pagination": {
    "page": 1,
    "per_page": 25
  }
}
```

### Request Rules

| Field | Required | Validation |
| --- | --- | --- |
| `filters.industry` | Yes | String, 2-100 characters after trimming. |
| `filters.country` | Yes | String, 2-100 characters after trimming. |
| `filters.state` | Yes | String, 1-100 characters after trimming. |
| `filters.city` | Yes | String, 1-100 characters after trimming. |
| `pagination.page` | No | Integer, minimum `1`, default `1`. |
| `pagination.per_page` | No | Integer, `1` through `100`, default `25`. |

Unknown request fields must be rejected with `VALIDATION_ERROR`.

### Success Response

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "name": "ABC Fitness",
        "industry": "gym",
        "website": "https://abcfitness.example",
        "phone": "+123456789",
        "email": "contact@abcfitness.example",
        "country": "United States",
        "state": "Texas",
        "city": "Houston",
        "address": "123 Main Street",
        "source_type": "directory"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 25,
      "total": 42,
      "total_pages": 2,
      "has_next": true,
      "has_previous": false
    }
  },
  "message": null,
  "request_id": "..."
}
```

### Empty Results Response

```json
{
  "success": true,
  "data": {
    "results": [],
    "pagination": {
      "page": 1,
      "per_page": 25,
      "total": 0,
      "total_pages": 0,
      "has_next": false,
      "has_previous": false
    }
  },
  "message": null,
  "request_id": "..."
}
```

### Search Logging

Each accepted search request must insert one row into `search_logs`.

Fields:

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

### Audit Logging

Each successful search request must insert one audit event.

Event type:

```text
business_search
```

Metadata:

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

## 6. Get Search History

Endpoint:

```text
GET /api/v1/search/history
```

Authentication:

```text
Required
```

Permission:

```text
search:history
```

CSRF:

```text
Not required for GET
```

### Query Parameters

| Parameter | Default | Validation |
| --- | --- | --- |
| `page` | `1` | Integer, minimum `1`. |
| `per_page` | `25` | Integer, `1` through `100`. |

### Success Response

```json
{
  "success": true,
  "data": {
    "history": [
      {
        "id": "uuid",
        "industry": "gym",
        "country": "United States",
        "state": "Texas",
        "city": "Houston",
        "results_count": 42,
        "created_at": "2026-06-25T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 25,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  },
  "message": null,
  "request_id": "..."
}
```

Search history is scoped to the authenticated user. Users must not receive search history created by other users.

## 7. Get Business Detail

Endpoint:

```text
GET /api/v1/businesses/{id}
```

Authentication:

```text
Required
```

Permission:

```text
business:read
```

CSRF:

```text
Not required for GET
```

### Path Parameters

| Parameter | Validation |
| --- | --- |
| `id` | Valid UUID. |

### Success Response

```json
{
  "success": true,
  "data": {
    "business": {
      "id": "uuid",
      "name": "ABC Fitness",
      "industry": "gym",
      "website": "https://abcfitness.example",
      "phone": "+123456789",
      "email": "contact@abcfitness.example",
      "country": "United States",
      "state": "Texas",
      "city": "Houston",
      "address": "123 Main Street",
      "description": "Local fitness business.",
      "source_type": "directory",
      "contacts_count": 2,
      "sources_count": 1,
      "social_profiles_count": 1
    }
  },
  "message": null,
  "request_id": "..."
}
```

### Not Found Response

```json
{
  "success": false,
  "error": {
    "code": "BUSINESS_NOT_FOUND",
    "message": "Business not found."
  },
  "request_id": "..."
}
```

## 8. Get Business Contacts

Endpoint:

```text
GET /api/v1/businesses/{id}/contacts
```

Authentication:

```text
Required
```

Permission:

```text
contact:read
```

### Query Parameters

| Parameter | Default | Validation |
| --- | --- | --- |
| `page` | `1` | Integer, minimum `1`. |
| `per_page` | `25` | Integer, `1` through `100`. |

### Success Response

```json
{
  "success": true,
  "data": {
    "business_id": "uuid",
    "contacts": [
      {
        "id": "uuid",
        "full_name": "Public Contact",
        "role": "Support",
        "email": "support@abcfitness.example",
        "phone": "+123456789",
        "source_url": "https://abcfitness.example/contact",
        "created_at": "2026-06-25T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 25,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  },
  "message": null,
  "request_id": "..."
}
```

## 9. Get Business Sources

Endpoint:

```text
GET /api/v1/businesses/{id}/sources
```

Authentication:

```text
Required
```

Permission:

```text
source:read
```

### Query Parameters

| Parameter | Default | Validation |
| --- | --- | --- |
| `page` | `1` | Integer, minimum `1`. |
| `per_page` | `25` | Integer, `1` through `100`. |

### Success Response

```json
{
  "success": true,
  "data": {
    "business_id": "uuid",
    "sources": [
      {
        "id": "uuid",
        "source_type": "directory",
        "source_url": "https://directory.example/abc-fitness",
        "trust_tier": "B",
        "confidence_score": 80,
        "collected_at": "2026-06-25T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 25,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  },
  "message": null,
  "request_id": "..."
}
```

## 10. Error Codes

| Condition | HTTP Status | Error Code |
| --- | --- | --- |
| Unauthenticated request | `401` | `AUTHENTICATION_REQUIRED` |
| Invalid access token | `401` | `INVALID_ACCESS_TOKEN` |
| Missing permission | `403` | `PERMISSION_DENIED` |
| CSRF validation failure | `403` | `CSRF_VALIDATION_FAILED` |
| Invalid request body or query params | `422` | `VALIDATION_ERROR` |
| Business not found | `404` | `BUSINESS_NOT_FOUND` |
| Rate limit exceeded | `429` | `RATE_LIMIT_EXCEEDED` |
| Unexpected failure | `500` | `INTERNAL_SERVER_ERROR` |

## 11. Security Requirements

* All endpoints in this document require authentication.
* `POST /api/v1/search` requires CSRF validation.
* `GET` endpoints do not require CSRF validation.
* All endpoints must enforce RBAC permissions from `rbac-permissions-matrix.md`.
* All endpoints must include `request_id` in success and error responses.
* All errors must be sanitized.
* Search request bodies must never include secrets or tokens.
* Audit metadata must never include secrets, tokens, raw cookies, or passwords.

## 12. Rate Limiting

All endpoints in this document use the project default limits:

```text
60 requests/minute per user
1000 requests/day per user
```

Rate limited responses must use HTTP `429` and the standard error wrapper.

## 13. Implementation Notes

* Use existing SQLAlchemy models and repositories.
* Add repository methods for filtered business search, count, and relationship list pagination.
* Keep route handlers thin.
* Keep business logic in services.
* Use existing authentication dependencies.
* Use existing audit log repository.
* Use existing `search_logs` table for accepted searches.
* `search_logs.user_id` and `search_logs.request_id` are required for user-scoped history and request traceability.
* Do not introduce new infrastructure or external services for V1 search.
