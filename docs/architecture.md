# System Architecture (V1)

## 1. Overview

This document defines the high-level architecture of the Lead Generator App.

The system is designed as a modular, containerized SaaS platform that performs:

* Business discovery
* Business detail lookup
* Public contact information collection
* Lead export

The system is optimized for:

* Local-first development (Docker Compose)
* Low cost operation (no mandatory paid APIs)
* Future scalability (worker-based architecture)

MVP scope includes business search, business details, contact information from public sources, and CSV export. Phase 4 is limited to public data acquisition and must not add decision-maker identification, opportunity scoring, or AI enrichment.

---

# 2. High-Level Architecture

## System Diagram

```text id="sys-arch"
                 ┌──────────────────────┐
                 │     Next.js UI       │
                 │  (Dashboard Frontend)│
                 └─────────┬────────────┘
                           │ HTTPS API Calls
                           ▼
                 ┌──────────────────────┐
                 │   FastAPI Backend    │
                 │  (Core API Layer)    │
                 └─────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ Worker       │  │ External Web │
│ Database     │  │ Service      │  │ Sources      │
└──────────────┘  │ (Jobs)       │  └──────────────┘
                  └──────────────┘
```

---

# 3. Core System Components

## 3.1 Frontend (Next.js)

Technology:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* React Query

Responsibilities:

* Search interface
* Lead dashboard
* Filters (industry, country, city)
* Results visualization
* Export UI

Communication:

* Talks only to FastAPI backend via HTTPS

---

## 3.2 Backend API (FastAPI)

Technology:

* FastAPI
* Pydantic validation
* JWT authentication

Responsibilities:

* Business search
* Data retrieval
* Trigger background jobs
* Serve processed leads
* Export CSV data

Security:

* JWT authentication
* Rate limiting
* Role-based access control

---

## 3.3 Database (PostgreSQL)

Responsibilities:

* Store all business data
* Store contacts
* Maintain source traceability

Every collected contact is traced by `business_id`, `source_id`, and `collection_timestamp`.

Key Design:

* Business-centric relational model
* Indexed for location + industry queries
* JSONB for job payloads and operational metadata

---

## 3.4 Worker Service (Background Processing)

Technology:

* Python worker service
* Async job execution

Responsibilities:

* Website crawling
* Contact extraction from public sources
* CSV export preparation

Execution Model:

* Triggered via API
* Runs async jobs
* Updates database after processing

---

## 3.5 External Data Sources Layer

Sources include:

* Public business directories
* Company websites
* Search engine results (light usage)
* Public contact pages

Rules:

* No paid datasets in V1
* No LinkedIn scraping dependency
* Only publicly accessible data

---

# 4. Data Flow Architecture

## 4.1 Search Flow

```text id="flow-search"
User → Next.js UI
     → FastAPI /api/v1/search endpoint
     → PostgreSQL query
     → Return cached + collected results
     → UI renders leads
```

---

## 4.2 Contact Collection Flow

```text id="flow-contact-collection"
API Trigger
   ↓
Database-backed job queue
   ↓
Public website crawling
   ↓
Public contact extraction
   ↓
Database update
```

---

## 4.3 MVP Boundary

Phase 4 worker flows are limited to public contact collection, source traceability, CSV export background processing, and allowed background job execution.

CSV export background processing is part of the MVP. Export requests create one export record and one `csv_export` background job.

---

# 5. Security Architecture

## 5.1 Authentication Layer

* JWT access token authentication
* Opaque refresh tokens
* HTTP-only secure cookies
* CSRF protection for state-changing browser requests
* Expiring sessions

---

## 5.2 API Security Layer

All endpoints protected by:

* Authentication middleware
* Rate limiting
* Input validation
* Request logging

---

## 5.3 Internal Service Protection

Worker endpoints:

* NOT publicly accessible
* Internal network only (Docker network)
* Authenticated with `INTERNAL_API_TOKEN`
* Successful internal token validation resolves to the `system_worker` identity
* Authorized with worker-specific RBAC permissions

---

## 5.4 Network Security

* HTTPS only (TLS)
* No direct DB exposure outside container network
* Isolated Docker network per service

---

## 5.5 Abuse Protection

* Rate limiting per user
* IP tracking
* Request throttling
* Query complexity limits

---

# 6. Docker Compose Architecture

## Services

```yaml id="docker-arch"
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  worker:
    build: ./worker
    depends_on:
      - backend
      - postgres

  postgres:
    image: postgres:15.5
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    expose:
      - "5432"
```

---

# 7. System Design Principles

## 7.1 Modular Architecture

Each component is independent:

* UI does not know scraping logic
* API does not handle crawling directly
* Workers handle heavy tasks

---

## 7.2 Asynchronous Processing

Heavy tasks are handled via worker service:

* public contact collection
* crawling
* CSV export generation

---

## 7.3 Single Source of Truth

PostgreSQL is the only persistent storage layer.

---

## 7.4 Cost Efficiency

* No paid APIs required in V1
* No external SaaS dependency
* Local-first deployment

---

## 7.5 Scalability Path

Future upgrades:

* Redis queue (job scaling)
* Kubernetes deployment
* Microservices split
* API gateway (Kong / Nginx)
* Multi-tenant SaaS layer

---

# 8. Performance Strategy

* Indexed queries for (country, city, industry)
* Cached search results
* Batch public contact collection
* Pagination for all API responses

---

# 9. Failure Handling Strategy

* Worker retries on failure
* Dead-letter job handling
* Graceful API degradation
* Partial contact collection fallback allowed

---

# 10. V1 System Constraints

* Single-region deployment
* No distributed system complexity
* No multi-cloud setup
* No Kubernetes in V1
* No external paid data APIs

---

# 11. Summary

This architecture provides:

* A fully working lead intelligence system
* Modular and scalable design
* Secure API-first backend
* Worker-based background processing pipeline
* Low-cost local development setup
* Future SaaS expansion path
