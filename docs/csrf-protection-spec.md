# CSRF Protection Specification (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines CSRF protection for the FastAPI backend and Next.js frontend.

Authentication uses HTTP-only secure cookies, so CSRF protection is required for state-changing browser requests.

---

# 2. Pattern

Use the CSRF Token Header pattern.

The backend issues a CSRF token as a non-HTTP-only cookie.

The frontend reads that CSRF cookie and sends it back on state-changing requests using:

```text
X-CSRF-Token
```

Authentication tokens remain HTTP-only and are never readable by JavaScript.

---

# 3. Token Generation

The backend generates a cryptographically random CSRF token when:

* a user registers
* a user logs in
* a session is refreshed
* the frontend requests a new CSRF token

The CSRF token must be bound to the current authenticated session on the backend.

---

# 4. Cookie Settings

CSRF cookie:

```text
HttpOnly=false
Secure=true in production
SameSite=Lax by default
Path=/
```

Authentication cookies:

```text
HttpOnly=true
Secure=true in production
SameSite=Lax by default
Path=/
```

`SameSite` and `Secure` must be configurable by environment.

---

# 5. Frontend Requirements

The Next.js frontend must:

* read the CSRF cookie
* send `X-CSRF-Token` on state-changing requests
* never read authentication cookies
* never store authentication tokens in localStorage
* never store authentication tokens in sessionStorage

State-changing methods include:

```text
POST
PUT
PATCH
DELETE
```

---

# 6. Backend Validation Flow

For each state-changing browser request:

1. Read the CSRF cookie.
2. Read the `X-CSRF-Token` header.
3. Compare both values using constant-time comparison.
4. Verify the token is valid for the current session.
5. Reject the request if validation fails.

Safe methods such as `GET`, `HEAD`, and `OPTIONS` do not require CSRF validation.

---

# 7. CSRF Refresh Endpoint

Endpoint:

```text
GET /api/v1/auth/csrf
```

Returns a standard success response and sets or refreshes the CSRF cookie.

Response:

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

---

# 8. Error Response

Failed CSRF validation returns HTTP `403`.

Response:

```json
{
  "success": false,
  "error": {
    "code": "CSRF_VALIDATION_FAILED",
    "message": "CSRF validation failed."
  },
  "request_id": "..."
}
```

---

# 9. Logging

CSRF failures must be logged as security events with:

* user_id when available
* request_id
* ip_address
* timestamp
* action

