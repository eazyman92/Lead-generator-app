# Architecture Decisions

## ADR-001

Database Technology

Decision:
PostgreSQL 15.5

Reason:

* Open source
* Reliable
* ACID compliant
* Strong indexing support
* SQLAlchemy support

---

## ADR-002

Containerization

Decision:
Docker Compose

Reason:

* Local development simplicity
* Fast onboarding
* One-command startup
* Easy migration to Kubernetes later

---

## ADR-003

Backend Framework

Decision:
FastAPI

Reason:

* Async support
* Automatic OpenAPI docs
* Strong typing
* High performance

---

## ADR-004

Frontend Framework

Decision:
Next.js + TypeScript + Tailwind

Reason:

* Modern UI
* SSR support
* Strong ecosystem
* Excellent developer experience

---

## ADR-005

Database Exposure

Decision:
PostgreSQL remains internal-only.

Implementation:

expose:

* "5432"

Reason:
Prevent direct internet access.

---

## ADR-006

Secrets Management

Decision:
No hardcoded secrets.

Implementation:
.env variables only.

Reason:
Security compliance.

---

## ADR-007

Authentication Strategy

Decision:
JWT Access Token + Opaque Refresh Token.

Reason:
Secure session management.

---

## ADR-008

Worker Architecture

Decision:
Database-backed job queue.

Reason:
No external infrastructure required during MVP.
