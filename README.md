# Lead Generator App

Lead Generator App is a full-stack platform for discovering businesses, collecting publicly available contact information, and exporting MVP lead data. The project is being built in phased milestones, with the current foundation covering repository scaffolding, database models and migrations, authentication, authorization, and security audit hardening.

The MVP goal is to support:

* Business search by industry and location
* Business detail views
* Contact information from public sources
* CSV export

Future releases may add decision-maker enrichment, scoring, and advanced intelligence workflows.

## Current Status

* Phase 0 Bootstrap ✅
* Phase 1 Database Foundation ✅
* Phase 2 Authentication & Security ✅
* Phase 3 Search Engine ⏳ Planned
* Phase 4 Lead Acquisition ⏳ Planned
* Phase 5 Export System ⏳ Planned
* Phase 6 Frontend Dashboard ⏳ Planned

## Tech Stack

### Frontend

* Next.js
* TypeScript
* TailwindCSS

### Backend

* FastAPI
* SQLAlchemy 2.x
* Alembic

### Database

* PostgreSQL 15.5

### Security

* JWT Access Tokens
* Opaque Refresh Tokens
* Refresh Token Rotation
* Refresh Token Reuse Detection
* Argon2id Password Hashing
* HTTP-only Cookies
* CSRF Protection
* RBAC
* Audit Logging

### Infrastructure

* Docker
* Docker Compose

## Repository Structure

```text
lead-generator-app/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   `-- services/
|   |-- tests/
|   |-- Dockerfile
|   `-- requirements.txt
|-- config/
|-- database/
|   |-- backups/
|   `-- migrations/
|       `-- versions/
|-- docker/
|-- docs/
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   `-- styles/
|   |-- Dockerfile
|   |-- package.json
|   |-- tailwind.config.ts
|   `-- tsconfig.json
|-- logs/
|-- scripts/
|-- tests/
|-- uploads/
|-- worker/
|   |-- config/
|   |-- tests/
|   |-- Dockerfile
|   |-- main.py
|   `-- requirements.txt
|-- .env.example
|-- alembic.ini
|-- docker-compose.yml
|-- pyproject.toml
`-- README.md
```

## Implemented Features

### Authentication

* Register
* Login
* Logout
* Logout All
* Refresh Token
* Current User Endpoint
* CSRF Endpoint

Implemented authentication endpoints:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
GET  /api/v1/auth/csrf
```

### Database

* Users
* Refresh Tokens
* Businesses
* Contacts
* Data Sources
* Social Profiles
* Search Logs
* Exports
* Background Jobs
* Audit Logs

## Running Locally

1. Create a local environment file from the example:

```bash
cp .env.example .env
```

2. Fill in the placeholder values in `.env`.

3. Build and start the containers:

```bash
docker compose up -d --build
```

4. Apply database migrations from the repository root in an environment with the backend requirements installed:

```bash
alembic upgrade head
```

5. Check service health:

```bash
docker compose ps
```

Backend health:

```text
http://localhost:8000/health
```

Frontend:

```text
http://localhost:3000
```

To stop the local stack:

```bash
docker compose down
```

## Environment Variables

Environment variables are documented in:

```text
.env.example
```

Do not commit local `.env` files or real secret values.

## Security Notes

* No hardcoded secrets are required by the application.
* PostgreSQL is internal to the Docker network and is not publicly exposed.
* Authentication uses HTTP-only cookies for access and refresh tokens.
* Refresh tokens are opaque values and only their hashes are stored in the database.
* Refresh token rotation and reuse detection are implemented.
* Passwords are hashed with Argon2id.
* CSRF protection is required for state-changing authentication requests.
* RBAC permissions are documented in the permissions matrix.
* Authentication events, CSRF failures, and permission denials are audit logged.

## Documentation

Important documentation files:

* `docs/architecture.md`
* `docs/tech-stack.md`
* `docs/project-structure.md`
* `docs/implementation-roadmap.md`
* `docs/security-standards.md`
* `docs/api-spec.md`
* `docs/api-error-contract.md`
* `docs/data-model.md`
* `docs/database-erd.md`
* `docs/authentication-spec.md`
* `docs/authentication-implementation-design.md`
* `docs/refresh-token-spec.md`
* `docs/csrf-protection-spec.md`
* `docs/rbac-permissions-matrix.md`
* `docs/phase-1-validation-report.md`
* `docs/phase-2-auth-implementation-report.md`
* `docs/phase-2-auth-validation-report.md`
* `docs/phase-2-auth-audit-hardening-report.md`

## Next Milestone

Phase 3 Search Engine.

Phase 3 should focus on the backend search engine foundation for MVP business search. Business search, lead acquisition, export workflows, and frontend dashboard pages are not part of the completed Phase 2 implementation.
