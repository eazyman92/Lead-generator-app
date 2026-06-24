# Authentication Specification (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines authentication behavior for the Lead Generator App.

It resolves implementation details for:

* login
* registration
* JWT access tokens
* refresh tokens
* logout
* protected routes
* role-based access control

---

# 2. API Routes

Authentication routes use public API versioning:

```text
/api/v1/auth/*
```

Required routes:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
GET /api/v1/auth/me
```

---

# 3. Authentication Rules

The register, login, and refresh endpoints are authentication bootstrap endpoints.

They do not require an existing access token, but they must still use:

* rate limiting
* request validation
* request logging
* request_id tracing
* sanitized error responses
* CSRF validation where cookies are accepted

All other protected endpoints require a valid access token.

---

# 4. Token Standards

Access tokens:

* JWT
* lifetime: 15 minutes
* signed with `AUTH_JWT_SECRET_KEY`
* delivered using an HTTP-only secure cookie

Refresh tokens:

* opaque token
* lifetime: 30 days
* delivered using an HTTP-only secure cookie
* stored only as a hash in the database
* must be revocable on logout

Tokens must never be logged.

---

# 5. Token Storage

Required frontend storage:

* HTTP-only secure cookies

Required cookie settings:

* `HttpOnly=true`
* `SameSite=Lax` by default
* `Secure=true` in production

`SameSite` and `Secure` must be configurable by environment.

CSRF protection is required for state-changing requests.

Never store sensitive tokens in:

* localStorage
* sessionStorage
* browser-accessible JavaScript variables
* source code

---

# 6. Password Standards

Password hashing:

* Argon2id required
* bcrypt allowed only as fallback

Minimum password policy:

* 12 characters
* uppercase
* lowercase
* number

Plaintext passwords must never be stored or logged.

---

# 7. Required Environment Variables

Authentication requires:

```bash
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=
AUTH_JWT_SECRET_KEY=
AUTH_COOKIE_DOMAIN=
AUTH_COOKIE_SECURE=
AUTH_COOKIE_SAMESITE=
```

Application startup must fail if required authentication secrets are missing.

---

# 8. Roles

Supported roles:

```text
admin
user
system_worker
```

Protected endpoints must validate:

* identity
* role
* permissions

---

# 9. Standard Response Format

All authentication responses must use:

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

Authentication responses must not include access tokens or refresh tokens in JSON response bodies. Tokens are delivered only through HTTP-only secure cookies.

---

# 10. Related Specifications

Refresh token lifecycle is defined in `refresh-token-spec.md`.

CSRF protection is defined in `csrf-protection-spec.md`.
