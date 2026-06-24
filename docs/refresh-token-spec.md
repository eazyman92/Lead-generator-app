# Refresh Token Specification (V1)

## Project

Lead Generator App

---

# 1. Purpose

Define refresh token lifecycle management.

Authentication uses:

* Access Token (JWT)
* Refresh Token (Opaque Token)

Access tokens are short-lived.

Refresh tokens are used to obtain new access tokens without requiring user login.

---

# 2. Token Delivery

Use:

* HTTP-only Secure Cookie
* SameSite=Lax
* Secure=true in production
* HttpOnly=true

Tokens must never be stored in:

* localStorage
* sessionStorage
* browser-accessible JavaScript variables

---

# 3. Refresh Token Storage

Database Table:

```sql
refresh_tokens
```

Columns:

* id (UUID)
* user_id (UUID)
* token_hash (TEXT)
* issued_at (TIMESTAMP)
* expires_at (TIMESTAMP)
* revoked_at (TIMESTAMP NULL)
* replaced_by_token_id (UUID NULL)
* created_ip (VARCHAR)
* user_agent (TEXT)
* last_used_at (TIMESTAMP)

---

# 4. Security Rules

Never store raw refresh tokens.

Only store token hashes.

Database compromise must not expose usable refresh tokens.

---

# 5. Access Token Lifetime

15 minutes

Configurable using:

```text
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
```

---

# 6. Refresh Token Lifetime

30 days

Configurable using:

```text
AUTH_REFRESH_TOKEN_EXPIRE_DAYS
```

---

# 7. Refresh Flow

Endpoint:

```text
POST /api/v1/auth/refresh
```

Flow:

1. Validate token
2. Check not revoked
3. Check not expired
4. Issue new access token
5. Rotate refresh token
6. Revoke previous refresh token
7. Store new token hash

---

# 8. Logout Flow

Endpoint:

```text
POST /api/v1/auth/logout
```

Flow:

1. Revoke current refresh token
2. Clear cookies
3. Return success

---

# 9. Logout All Devices

Endpoint:

```text
POST /api/v1/auth/logout-all
```

Flow:

1. Revoke all active refresh tokens
2. Clear current cookies
3. Force re-authentication

---

# 10. Token Rotation

Every refresh operation must:

* Create new access token
* Create new refresh token
* Revoke previous refresh token

---

# 11. Refresh Token Reuse Detection

If a revoked token is reused:

1. Log security event
2. Revoke all active user sessions
3. Require re-authentication

Create audit log entry.

---

# 12. Cleanup Job

Worker:

```text
expired_refresh_token_cleanup
```

Runs daily.

Removes:

* expired refresh tokens
* revoked tokens beyond retention period

Retention:

```text
90 days
```

---

# 13. Audit Logging

Track:

* login
* logout
* logout-all
* refresh
* token reuse attempts

Required fields:

* user_id
* request_id
* ip_address
* timestamp
* action

---

# 14. Environment Variables

```text
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
AUTH_REFRESH_TOKEN_EXPIRE_DAYS
AUTH_JWT_SECRET_KEY
AUTH_COOKIE_DOMAIN
AUTH_COOKIE_SECURE
AUTH_COOKIE_SAMESITE
```

