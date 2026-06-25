# Security Standards (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines mandatory security requirements for:

* Frontend
* Backend
* Workers
* Database
* Docker Containers
* CI/CD Pipelines
* Future Production Deployments

Security requirements are mandatory and cannot be bypassed.

---

# 2. Security Principles

## Principle 1

Security by Design

Security must be implemented during development.

---

## Principle 2

Least Privilege

Users and services receive only the permissions they need.

---

## Principle 3

Zero Trust

No request, service, or user is trusted automatically.

Every interaction must be verified.

---

## Principle 4

Defense in Depth

Security must exist at multiple layers:

* Network
* Application
* Authentication
* Authorization
* Database

---

# 3. Authentication Standards

## Authentication Method

Required:

* JWT access tokens
* Opaque refresh tokens
* HTTP-only secure cookies
* CSRF protection

---

## Access Token Lifetime

```text id="7vk88n"
15 minutes
```

Configurable using:

```text
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
```

---

## Refresh Token Lifetime

```text id="ww8r23"
30 days
```

Configurable using:

```text
AUTH_REFRESH_TOKEN_EXPIRE_DAYS
```

---

## Token Storage

Frontend:

* HTTP-only secure cookies required
* HttpOnly=true
* SameSite=Lax by default
* Secure=true in production

Never:

* localStorage for sensitive tokens
* sessionStorage for sensitive tokens
* browser-accessible JavaScript variables for sensitive tokens

Tokens must never be returned in JSON response bodies.

---

# 4. Password Security

## Password Storage

Passwords must never be stored in plaintext.

---

## Required Algorithm

Use:

```text id="qrz0ns"
Argon2id
```

Fallback:

```text id="e7ag5u"
bcrypt
```

---

## Minimum Password Policy

Minimum:

```text id="0bhyqs"
12 characters
```

Require:

* uppercase
* lowercase
* number

---

# 5. Authorization Standards

## Role-Based Access Control

Roles:

```text id="v6wpdg"
admin

user

system_worker
```

---

## Authorization Enforcement

Every protected endpoint must verify:

```text id="pzmyl4"
identity

role

permissions
```

before execution.

---

# 6. API Security Standards

## HTTPS Only

All traffic encrypted.

Exception:

Localhost development may use HTTP only for local testing. Staging, production, and any non-local deployment must use HTTPS.

---

## TLS Version

Minimum:

```text id="vutryg"
TLS 1.2
```

Preferred:

```text id="wd1e4z"
TLS 1.3
```

---

## API Versioning

Required:

```text id="l4i1el"
/api/v1/
```

Internal APIs must use:

```text
/internal/v1/
```

---

## Input Validation

All inputs validated using:

* Pydantic schemas
* Length limits
* Type checks

---

## Output Validation

Responses must never expose:

* stack traces
* database errors
* secrets

---

# 7. Rate Limiting Standards

Default Limits:

```text id="6vnd6m"
60 requests/minute
```

Per User

---

Daily Limit:

```text id="l25sgw"
1000 requests/day
```

---

Abuse Detection:

* repeated failures
* excessive scraping
* unusual request patterns

must trigger throttling.

---

# 8. Security Headers

Required Headers:

```text id="uh6ibn"
Strict-Transport-Security

X-Frame-Options

X-Content-Type-Options

Referrer-Policy

Content-Security-Policy
```

---

# 9. CORS Policy

Default:

```text id="l7pg4x"
deny all
```

---

Explicitly allow:

```text id="h45z5s"
frontend domain(s)
```

only.

---

Never:

```text id="1p4xtl"
allow *
```

in production.

---

# 10. Content Security Policy

Restrict:

* scripts
* images
* frames
* external resources

to approved domains only.

---

# 11. Secrets Management

## Rule

No secrets in source code.

---

Secrets must come from:

```text id="od7sxw"
environment variables
```

or future secret management systems.

---

## Prohibited

Never commit:

```text id="1ec3e0"
API keys

JWT secrets

database passwords

encryption keys
```

---

# 12. Environment Validation

Application startup must fail if:

```text id="4kh1hk"
required variables missing
```

Example:

```text id="6f60wp"
DATABASE_URL

AUTH_JWT_SECRET_KEY

AUTH_ACCESS_TOKEN_EXPIRE_MINUTES

AUTH_REFRESH_TOKEN_EXPIRE_DAYS

AUTH_COOKIE_SECURE

AUTH_COOKIE_SAMESITE

AUTH_COOKIE_DOMAIN

POSTGRES_PASSWORD
```

---

# 13. Database Security Standards

## Database Exposure

PostgreSQL must never be publicly exposed.

---

Access allowed only from:

```text id="36n0gw"
backend

worker
```

containers.

---

## Credentials

Separate credentials for:

```text id="g5xygt"
application

administration

migration jobs
```

---

## Encryption

Sensitive data encrypted at rest.

Examples:

* contact emails
* user emails
* API credentials

Phase 4 contact collection ownership:

* Contact email and phone encryption is owned by the repository persistence boundary.
* Contact collection services must normalize values before persistence.
* Repositories must encrypt contact email and phone before insert/update and decrypt only for authorized API/service responses.
* `ENCRYPTION_KEY` is required for contact-field encryption.
* Raw contact values must not be stored in job payloads, logs, audit metadata, or error messages.

---

# 14. Audit Logging Standards

All security events logged.

---

Events:

```text id="k11a8n"
login success

login failure

permission denied

token refresh

account changes

logout

logout-all

token reuse attempt
```

---

Required Fields:

```text id="w1ik5v"
timestamp

user_id

event_type

ip_address

request_id
```

---

# 15. Worker Security Standards

Workers must:

* run with least privilege
* use dedicated service accounts
* access only required APIs

---

Worker endpoints:

```text id="2v2p7x"
/internal/v1/*
```

must never be public.

---

# 16. Container Security Standards

## Base Images

Use:

```text id="yy9npx"
official images only
```

---

Avoid:

```text id="4jcw5o"
unmaintained images
```

---

## Containers

Must run:

```text id="4lnmcm"
non-root
```

where possible.

---

## Filesystem

Use:

```text id="m76vta"
read-only
```

where practical.

---

# 17. Docker Network Security

Services communicate through:

```text id="c9nn0d"
private Docker network
```

---

Only frontend and backend expose ports.

---

Database must remain internal.

---

# 18. Logging Security

Never log:

```text id="8kcx5n"
passwords

tokens

secrets

API keys
```

---

Sensitive values must be masked.

---

# 19. File Upload Security

Uploads must be validated.

---

Check:

* extension
* MIME type
* file size

---

Reject:

* executable files
* scripts
* suspicious content

---

# 20. Dependency Security

Every build must scan:

Frontend:

```text id="nq4qhy"
npm audit
```

---

Backend:

```text id="kzy51x"
pip-audit
```

---

Container Images:

```text id="l4d2yn"
Trivy
```

---

# 21. Backup Security

Backups must be:

* encrypted
* access controlled

---

Retention:

```text id="6wsn7f"
30 days
```

minimum.

---

# 22. Incident Response Requirements

Must support:

* log review
* user activity tracing
* rollback procedures

---

Security incidents must be traceable.

---

# 23. Future Security Enhancements

Reserved for:

* MFA
* SSO
* OAuth2
* Hardware security keys
* Secret Vault Integration
* WAF
* SIEM Integration

---

# 24. Security Checklist

Before release:

✓ Authentication tested

✓ Authorization tested

✓ Secrets externalized

✓ TLS enabled

✓ Database protected

✓ Logs reviewed

✓ Dependencies scanned

✓ Containers scanned

✓ Rate limiting verified

✓ Audit logging enabled

---

# 25. Security Constitution

The platform shall:

1. Trust Nothing
2. Verify Everything
3. Encrypt Everywhere
4. Log Security Events
5. Minimize Privileges
6. Externalize Secrets
7. Protect User Data
8. Secure Containers
9. Secure APIs
10. Continuously Improve Security
