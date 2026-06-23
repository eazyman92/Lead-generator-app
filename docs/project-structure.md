# Project Structure & Engineering Standards (V1)

## Project

Lead Intelligence Platform

---

# 1. Purpose

This document defines:

* Repository structure
* Engineering standards
* Security standards
* Configuration management
* Coding conventions
* Deployment conventions
* Documentation standards

Every component of the platform must follow this document.

---

# 2. Engineering Principles

The platform shall be:

### Secure by Default

Security is not optional.

Every component must assume hostile traffic.

---

### Configuration Driven

Behavior must come from configuration.

Avoid hardcoded values.

---

### Modular

Components should be loosely coupled.

---

### Observable

Every service should produce logs and health metrics.

---

### Docker First

Every service must run inside containers.

---

### AI-Agent Friendly

Repository structure must be easy for:

* Codex
* AI coding agents
* Future contributors

to understand.

---

# 3. Repository Structure

```text
lead-intelligence-platform/

├── docs/
│
├── frontend/
│
├── backend/
│
├── worker/
│
├── database/
│
├── config/
│
├── docker/
│
├── scripts/
│
├── tests/
│
├── uploads/
│
├── logs/
│
├── .github/
│
├── .env.example
│
├── docker-compose.yml
│
└── README.md
```

---

# 4. Documentation Structure

```text
docs/

├── architecture.md
├── api-spec.md
├── data-model.md
├── data-acquisition-strategy.md
├── ui-ux-specification.md
├── project-structure.md
├── deployment-guide.md
├── security-standards.md
└── coding-standards.md
```

---

# 5. Frontend Structure

Technology:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

---

```text
frontend/

├── src/
│
├── app/
│
├── components/
│
├── features/
│
├── services/
│
├── hooks/
│
├── utils/
│
├── types/
│
├── assets/
│
├── styles/
│
└── tests/
```

---

# 6. Backend Structure

Technology:

* FastAPI

---

```text
backend/

├── app/
│
├── api/
│
├── services/
│
├── repositories/
│
├── models/
│
├── schemas/
│
├── middleware/
│
├── auth/
│
├── config/
│
├── utils/
│
└── tests/
```

---

# 7. Worker Structure

```text
worker/

├── jobs/
│
├── crawlers/
│
├── enrichers/
│
├── scoring/
│
├── schedulers/
│
├── config/
│
└── tests/
```

---

# 8. Database Structure

```text
database/

├── migrations/
│
├── seeds/
│
├── backups/
│
└── schemas/
```

---

# 9. Configuration Management

## Rule

No business logic may depend on hardcoded values.

---

## Configuration Folder

```text
config/

├── countries.json
├── states.json
├── industries.json
├── scoring-rules.json
├── feature-flags.json
└── ui-settings.json
```

---

# 10. Environment Variables

## Rule

All secrets must come from environment variables.

---

## Example

```bash
APP_ENV=

DATABASE_URL=

POSTGRES_USER=

POSTGRES_PASSWORD=

JWT_SECRET=

JWT_REFRESH_SECRET=

INTERNAL_API_TOKEN=

ENCRYPTION_KEY=
```

---

# 11. Secret Management Rules

## Never Allowed

Hardcoded:

* passwords
* API keys
* JWT secrets
* database credentials
* encryption keys

---

## Repository Rules

Must be ignored:

```text
.env
.env.local
.env.production
```

---

Only template files allowed:

```text
.env.example
```

---

# 12. Security Standards

All services must implement:

### Authentication

* JWT

---

### Authorization

* RBAC

---

### Encryption

* HTTPS/TLS
* Encryption at rest for sensitive data

---

### Validation

All incoming data validated.

---

### Logging

Security events logged.

---

# 13. Logging Standards

Every service must log:

```text
timestamp

service

level

message

correlation_id
```

---

## Log Levels

* INFO
* WARN
* ERROR
* SECURITY

---

# 14. API Standards

## Versioning

```text
/api/v1/
```

---

## Response Format

Success:

```json
{
  "success": true,
  "data": {}
}
```

---

Error:

```json
{
  "success": false,
  "error": "message"
}
```

---

# 15. Database Standards

## Primary Keys

Use UUIDs.

---

## Auditing Fields

Every table:

```sql
created_at

updated_at
```

---

## Soft Deletes

Preferred:

```sql
deleted_at
```

---

# 16. Frontend Standards

## Dynamic Assets

No hardcoded logos.

No hardcoded images.

---

Store assets in:

```text
/uploads
```

or future object storage.

---

## Dynamic Branding

Store:

* logo
* theme
* colors
* site name

in database settings.

---

# 17. Feature Flags

Feature management required.

---

Example:

```json
{
  "crm_module": false,
  "email_export": true,
  "ai_scoring": true
}
```

---

# 18. Testing Standards

Required:

### Backend

* Unit tests
* Integration tests

---

### Frontend

* Component tests

---

### Worker

* Job tests

---

# 19. Docker Standards

Every service must have:

```text
Dockerfile
```

---

Required containers:

```text
frontend

backend

worker

postgres
```

---

Single command startup:

```bash
docker compose up -d
```

---

Single command shutdown:

```bash
docker compose down
```

---

# 20. Health Checks

Every service must expose:

```text
/health
```

---

Response:

```json
{
  "status": "healthy"
}
```

---

# 21. CI/CD Readiness

Repository must support future:

* GitHub Actions
* Automated testing
* Security scanning
* Container builds

---

# 22. Naming Conventions

## Backend

snake_case

Example:

```python
business_service.py
```

---

## Frontend

PascalCase

Example:

```typescript
LeadTable.tsx
```

---

## APIs

kebab-case

Example:

```text
/api/business-search
```

---

# 23. Future Scalability

Reserved for:

* Redis
* Kubernetes
* Multi-tenancy
* API gateway
* Billing system
* CRM module

---

# 24. Definition of Done

A feature is complete only if:

✓ Documented

✓ Tested

✓ Secure

✓ Logged

✓ Configurable

✓ Containerized

✓ Reviewed

---

# 25. Project Constitution

The platform must always follow:

1. Security First
2. Configuration Over Hardcoding
3. Docker First
4. API First
5. Database Traceability
6. Modular Design
7. Observability
8. Maintainability
9. Scalability
10. AI-Agent Compatibility
