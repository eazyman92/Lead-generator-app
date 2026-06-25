# API Specification (V1)

## 1. Overview

This document defines secure API endpoints for the Lead Generator App.

All public API endpoints are:

* HTTPS only
* Authenticated via JWT
* Rate limited
* Logged for audit purposes

Authentication bootstrap endpoints are public but still rate limited, validated, and logged.

---

# 2. Authentication

Authentication uses HTTP-only secure cookies:

* Access Token: JWT
* Refresh Token: opaque token
* Cookie settings: `HttpOnly=true`, `SameSite=Lax` by default, `Secure=true` in production
* CSRF protection required for state-changing requests

Tokens must never be returned in JSON response bodies and must never be stored in `localStorage`, `sessionStorage`, or browser-accessible JavaScript variables.

---

## 2.1 Register

### Endpoint

```
POST /api/v1/auth/register
```

### Request

```json
{
  "email": "user@example.com",
  "password": "<user-provided-password>"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "user"
    }
  },
  "message": null,
  "request_id": "..."
}
```

---

## 2.2 Login

```
POST /api/v1/auth/login
```

Sets access and refresh cookies on successful authentication.

### Request

```json
{
  "email": "user@example.com",
  "password": "<user-provided-password>"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "user"
    }
  },
  "message": null,
  "request_id": "..."
}
```

---

## 2.3 Refresh Token

```
POST /api/v1/auth/refresh
```

Rotates the refresh token and sets new access and refresh cookies.

### Response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

---

## 2.4 Logout

```
POST /api/v1/auth/logout
```

Invalidates the current refresh token and clears authentication cookies.

### Response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

---

## 2.5 Logout All Devices

```
POST /api/v1/auth/logout-all
```

Invalidates all active refresh tokens for the current user and clears authentication cookies.

### Response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

---

## 2.6 Current User

```
GET /api/v1/auth/me
```

Returns the authenticated user profile.

### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "user"
    }
  },
  "message": null,
  "request_id": "..."
}
```

---

## 2.7 CSRF Token

```
GET /api/v1/auth/csrf
```

Sets or refreshes the CSRF cookie used by the frontend for state-changing requests.

### Response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

---

# 3. Security Middleware

Applied to all protected endpoints:

Every request must pass:

* JWT validation
* Rate limit check
* Role validation
* Request logging
* Input sanitization
* CSRF validation for state-changing browser requests

Authentication bootstrap endpoints must pass:

* Rate limit check
* Request logging
* Input sanitization
* CSRF validation where cookies are accepted

---

# 4. Business Search API

## 4.1 Search Businesses

```
POST /api/v1/search
```

### Auth Required: YES

### Request

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

### Response

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

## 4.2 Search History

```
GET /api/v1/search/history
```

### Auth Required: YES

### Query Parameters

* `page` - integer, minimum `1`, default `1`
* `per_page` - integer, `1` through `100`, default `25`

Returns user-scoped search history for the authenticated user.

### Response

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

---

# 5. Business Detail API

## 5.1 Get Business

```
GET /api/v1/businesses/{id}
```

### Auth Required: YES

Returns business info with related data counts.

### Response

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
      "created_at": "2026-06-25T00:00:00Z",
      "updated_at": "2026-06-25T00:00:00Z",
      "contacts_count": 2,
      "sources_count": 1,
      "social_profiles_count": 1
    }
  },
  "message": null,
  "request_id": "..."
}
```

---

# 6. Contact API

## 6.1 Get Contacts

```
GET /api/v1/businesses/{id}/contacts
```

Returns:

* public contacts
* roles
* emails if publicly available
* source URLs

### Query Parameters

* `page` - integer, minimum `1`, default `1`
* `per_page` - integer, `1` through `100`, default `25`

### Response

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
        "linkedin_url": null,
        "is_decision_maker": false,
        "priority_score": 0,
        "source_id": "uuid",
        "source_url": "https://abcfitness.example/contact",
        "collection_timestamp": "2026-06-25T00:00:00Z",
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

---

# 7. Export API

## 7.1 Export Leads

```
POST /api/v1/exports
```

### Auth Required: YES

### Request

```json
{
  "format": "csv",
  "filters": {
    "industry": "gym",
    "country": "UK"
  }
}
```

Creates an export record and one `csv_export` background job. CSV export generation is part of the MVP background job system.

### Response

```json
{
  "success": true,
  "data": {
    "export_id": "uuid",
    "job_id": "uuid",
    "status": "pending"
  },
  "message": null,
  "request_id": "..."
}
```

---

# 8. Data Source Tracking API

## 8.1 View Sources

```
GET /api/v1/businesses/{id}/sources
```

Returns:

* where data came from
* trust tier
* confidence score

### Query Parameters

* `page` - integer, minimum `1`, default `1`
* `per_page` - integer, `1` through `100`, default `25`

### Response

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

---

# 9. MVP Exclusions

The following are not part of V1 MVP APIs:

* decision-maker identification
* opportunity scoring
* AI enrichment
* website intelligence
* technology detection
* outreach automation

---

# 10. Internal System APIs (INTERNAL APIs)

These endpoints are NOT public.

Internal endpoints use `/internal/v1/*` and must be reachable only on the private service network.

Canonical internal security model:

* Authentication: `INTERNAL_API_TOKEN` in `X-Internal-API-Token`
* Identity: successful validation resolves to `system_worker`
* Authorization: worker-specific RBAC permissions
* Required tracing header: `X-Request-ID`

## 10.1 Create Contact Collection Job

```
POST /internal/v1/contact-collection
```

Required permission: `internal:contact_collection`

Creates or returns an existing idempotent `contact_collection` background job.

Active duplicate jobs are prevented by `ux_background_jobs_active_idempotency`.

## 10.2 Create CSV Export Job

```
POST /internal/v1/csv-export
```

Required permission: `internal:csv_export`

Creates or returns the single active `csv_export` background job for an export request.

Active duplicate jobs are prevented by `ux_background_jobs_active_idempotency`.

## 10.3 Get Job Status

```
GET /internal/v1/jobs/{job_id}
```

Required permission: `internal:job_read`

Returns status, attempts, retry metadata, cancellation metadata, and dead-letter metadata for a background job.

## 10.4 Retry Job

```
POST /internal/v1/jobs/{job_id}/retry
```

Required permission: `internal:job_retry`

Creates a new retry job from a sanitized failed or dead-lettered job payload. The original job remains immutable.

## 10.5 Cancel Job

```
POST /internal/v1/jobs/{job_id}/cancel
```

Required permission: `internal:job_cancel`

Cancels a cancellable pending or running job. Cancellation is represented as `status = "failed"` with `payload.cancelled = true` and `payload.dead_letter = false`.

## 10.6 Internal Job Error Codes

Canonical job error codes:

* `INVALID_PAYLOAD`
* `BUSINESS_NOT_FOUND`
* `PROHIBITED_SOURCE`
* `ROBOTS_DENIED`
* `SOURCE_AUTH_REQUIRED`
* `SOURCE_FORBIDDEN`
* `SOURCE_BLOCKED`
* `UNSUPPORTED_CONTENT_TYPE`
* `NETWORK_TIMEOUT`
* `DNS_FAILURE`
* `HTTP_429`
* `HTTP_5XX`
* `MAX_ATTEMPTS_EXCEEDED`
* `JOB_NOT_FOUND`
* `JOB_NOT_RETRYABLE`
* `JOB_NOT_CANCELLABLE`
* `JOB_CANCELLED`
* `UNKNOWN_JOB_TYPE`

Detailed internal API request and response contracts are defined in `internal-api-contracts.md`.

---

# 11. Security Controls

## 11.1 Rate Limiting

* 60 requests/min per user
* 1000 requests/day per user

---

## 11.2 IP Monitoring

* Block suspicious IPs
* Detect scraping patterns
* Auto-throttle abusive behavior

---

## 11.3 Audit Logging

Every request logs:

* user_id
* endpoint
* timestamp
* IP address
* response status
* request_id

---

## 11.4 Data Protection

* No raw database exposure
* No direct SQL access from API layer
* Sanitized outputs only

---

## 11.5 Encryption

* TLS 1.2+ required
* Sensitive fields encrypted at rest where required by `security-standards.md`
* Phase 4 contact email and phone values are encrypted at the repository persistence boundary using `ENCRYPTION_KEY`
* Traceability fields such as `source_id`, `source_url`, and `collection_timestamp` remain queryable

---

# 12. Role-Based Access Control (RBAC)

| Role          | Permissions                |
| ------------- | -------------------------- |
| user          | search, view, export       |
| admin         | manage permitted user-facing and internal MVP workflows |
| system_worker | internal pipelines only    |

---

# 13. API Design Principles

* No protected endpoint without authentication
* No unbounded queries
* No raw scraping exposure
* No public access to internal pipelines
* All outputs must be structured JSON

---

# 14. Error Response Format

All errors must use:

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

---

# 15. V1 Security Summary

This API is designed to:

* prevent abuse
* protect data integrity
* ensure traceability
* limit scraping attacks
* enforce controlled internal worker access
* support future scaling

---

# 16. Future Enhancements (NOT V1)

* API gateway (Kong / AWS API Gateway)
* OAuth2 login (Google / GitHub)
* Webhooks system
* API usage billing
* Multi-tenant workspace isolation
* Advanced anomaly detection
