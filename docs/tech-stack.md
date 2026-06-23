# Technology Stack (V1)

## Project

Lead Intelligence Platform

---

# 1. Purpose

This document defines the **single source of truth** for all technologies used in the system.

It ensures:

* consistency across all services
* no random library selection by AI or developers
* predictable architecture
* maintainable and scalable system design

---

# 2. Core Architecture Summary

```text id="stack-core"
Frontend → Next.js
Backend → FastAPI
Database → PostgreSQL
Workers → Python async services
Infra → Docker Compose
```

---

# 3. Frontend Stack

## 3.1 Framework

* Next.js (App Router)

Next.js

---

## 3.2 Language

* TypeScript

TypeScript

---

## 3.3 UI Framework

* Tailwind CSS

Tailwind CSS

---

## 3.4 Component System

* shadcn/ui
* Radix UI primitives

---

## 3.5 State Management

* React Query (TanStack Query)
* React Context (lightweight global state)

---

## 3.6 Frontend Responsibilities

* Lead search UI
* Dashboard UI
* Filtering system
* Lead detail pages
* Export interface
* Authentication UI

---

# 4. Backend Stack

## 4.1 Framework

* FastAPI

FastAPI

---

## 4.2 Language

* Python 3.11+

---

## 4.3 Validation Layer

* Pydantic

---

## 4.4 Authentication

* JWT (Access + Refresh tokens)

---

## 4.5 Backend Responsibilities

* Business search logic
* API orchestration
* Authentication & authorization
* Trigger enrichment jobs
* Serve processed leads

---

# 5. Worker / Background Processing Stack

## 5.1 Runtime

* Python async workers

---

## 5.2 Responsibilities

* Website crawling
* Data extraction
* Contact discovery
* Decision-maker identification
* Opportunity scoring

---

## 5.3 Execution Model

* Stateless workers
* Triggered via backend API
* Runs background jobs asynchronously

---

## 5.4 Queue System (V1 Design)

No external queue required initially.

Instead:

* database-backed job table
* polling worker system

---

# 6. Database Stack

## 6.1 Database Engine

* PostgreSQL

PostgreSQL

---

## 6.2 ORM

* SQLAlchemy (backend ORM)

---

## 6.3 Migrations

* Alembic

---

## 6.4 Data Features Used

* relational modeling
* JSONB for enrichment data
* indexing for search optimization

---

## 6.5 Database Responsibilities

* store all businesses
* store contacts
* store enrichment data
* store opportunity scores
* store sources & audit logs

---

# 7. Infrastructure Stack

## 7.1 Containerization

* Docker

Docker

---

## 7.2 Orchestration (V1)

* Docker Compose

---

## 7.3 Networking

* internal Docker bridge network
* no public DB exposure

---

## 7.4 Reverse Proxy (Future)

* Nginx (planned)

---

## 7.5 Hosting (V1)

* local machine / single server deployment

---

# 8. API & Communication Stack

## 8.1 API Style

* REST API (JSON-based)

---

## 8.2 Internal Communication

* HTTP between services
* internal-only endpoints for workers

---

## 8.3 API Security

* JWT authentication
* RBAC authorization
* rate limiting

---

# 9. Authentication & Security Stack

## 9.1 Auth System

* JWT (Access + Refresh tokens)

---

## 9.2 Password Hashing

* Argon2id

---

## 9.3 Security Middleware

* request validation
* CORS policy enforcement
* rate limiting layer

---

# 10. DevOps & Tooling Stack

## 10.1 Container Tooling

* Docker Compose

---

## 10.2 Environment Management

* .env files
* environment variable injection

---

## 10.3 Logging

* structured JSON logs

---

## 10.4 Testing

* Pytest (backend)
* Jest / React Testing Library (frontend)

---

## 10.5 Linting

* ESLint (frontend)
* Black + Ruff (backend)

---

## 10.6 Security Scanning

* pip-audit
* npm audit
* Trivy (containers)

---

# 11. Observability Stack (V1 Minimal)

* console logging
* health endpoints (/health)

Future:

* Prometheus
* Grafana
* Loki

---

# 12. File Storage Stack

## V1

* Local filesystem

---

## Future

* S3-compatible object storage

---

# 13. Feature Flags System

* JSON-based configuration system
* stored in /config/feature-flags.json
* runtime-loaded by backend

---

# 14. Configuration System

All system configuration must be:

* externalized
* environment-driven
* runtime-loadable where possible

No hardcoded values allowed.

---

# 15. Version Constraints

## Frontend

* Node.js 18+

---

## Backend

* Python 3.11+

---

## Database

* PostgreSQL 15+

---

## Docker

* Docker Engine 24+

---

# 16. Core Engineering Rule

The system must ALWAYS follow:

### No dynamic tech changes during runtime design

Meaning:

* stack is fixed
* libraries are fixed
* no ad-hoc additions during development

---

# 17. System Boundaries

## Allowed to change via config:

* UI branding
* scoring weights
* feature flags
* country/industry data

## NOT allowed to change via config:

* core architecture
* programming languages
* database engine
* API framework

---

# 18. Final Stack Summary

```text id="final-stack"
Frontend: Next.js + TypeScript + Tailwind + React Query

Backend: FastAPI + Python + Pydantic + SQLAlchemy

Database: PostgreSQL + Alembic

Workers: Python async services

Infra: Docker + Docker Compose

Auth: JWT + Argon2id

Testing: Pytest + Jest

Linting: ESLint + Ruff

Logging: Structured JSON logs
```

---

# 19. Stack Constitution

The system must:

1. Use only approved technologies
2. Avoid runtime architectural changes
3. Remain Docker-compatible
4. Remain environment-driven
5. Avoid hardcoded dependencies
6. Ensure reproducibility
7. Maintain simplicity in V1
