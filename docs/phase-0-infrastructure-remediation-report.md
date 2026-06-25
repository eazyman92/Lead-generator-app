# Phase 0 Infrastructure Remediation Report

Project: Lead Generator App

Date: 2026-06-25

Scope: Migration execution and runtime database initialization foundation only.

No Phase 4A Step 2 functionality was implemented. No contact collection, worker job execution, internal APIs, CSV export processing, enrichment, scoring, or frontend behavior was changed.

## Runtime Finding Reviewed

AWS validation revealed:

* PostgreSQL container was healthy.
* Backend container was healthy.
* Worker container was healthy.
* Alembic was installed inside the backend container.
* Database contained no tables.
* `alembic.ini` and `database/migrations` were not present inside the backend container.
* No service executed Alembic migrations.

## Root Cause

The backend image was built from `./backend` and copied only:

* `backend/requirements.txt`
* `backend/app`

The runtime image did not include:

* `alembic.ini`
* `database/migrations`

Alembic was installed but had no migration configuration or revision files to execute.

A secondary issue was identified: the project `DATABASE_URL` uses the asyncpg SQLAlchemy driver format, but the Alembic environment converted that URL to a synchronous PostgreSQL URL. The backend dependencies include `asyncpg`, not a synchronous PostgreSQL driver, so migration execution needed to use SQLAlchemy's async engine.

## Selected Long-Term Migration Strategy

The project now uses a dedicated Docker Compose migration service named `migrations`.

The migration service:

* builds from `backend/Dockerfile`
* uses the backend image
* includes backend models
* includes `alembic.ini`
* includes `database/migrations`
* depends on healthy PostgreSQL
* runs `alembic upgrade head`
* exits after completion
* does not publish ports

The backend service now waits for successful migration completion before startup.

## Files Modified

* `docker-compose.yml`
* `backend/Dockerfile`
* `database/migrations/env.py`

## Files Created

* `backend/tests/test_migration_execution_foundation.py`
* `docs/database-migration-strategy.md`
* `docs/migration-runbook.md`
* `docs/phase-0-infrastructure-remediation-report.md`

## Implementation Details

### Docker Compose

Added a `migrations` service.

The service runs:

```bash
alembic upgrade head
```

The backend service now depends on:

* `postgres` with `service_healthy`
* `migrations` with `service_completed_successfully`

### Backend Dockerfile

The backend image now builds from the repository root and copies:

* `backend/requirements.txt`
* `backend/app`
* `alembic.ini`
* `database/migrations`

This makes migration assets available at `/app/alembic.ini` and `/app/database/migrations`.

### Alembic Runtime

`database/migrations/env.py` now uses SQLAlchemy's async engine.

This preserves the existing `DATABASE_URL` format:

```text
postgresql+asyncpg://...
```

No synchronous PostgreSQL driver was added.

## Validation Instructions

Build images:

```bash
docker compose build
```

Run migrations:

```bash
docker compose run --rm migrations alembic upgrade head
```

Open PostgreSQL shell:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Verify all tables:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```

Expected tables:

* `alembic_version`
* `audit_logs`
* `background_jobs`
* `businesses`
* `contacts`
* `data_sources`
* `exports`
* `refresh_tokens`
* `search_logs`
* `social_profiles`
* `users`

## Tests Executed

```text
python -m py_compile database/migrations/env.py backend/tests/test_migration_execution_foundation.py
```

Result: passed

```text
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest backend/tests/test_migration_execution_foundation.py backend/tests/test_migration_definition.py -q
```

Result: 9 passed

```text
docker compose config --services
```

Result: passed. Services returned:

* `postgres`
* `migrations`
* `backend`
* `worker`
* `frontend`

Warnings were emitted because local Docker config access is restricted in this environment, but Compose still resolved the services.

## Docker Build Validation

Attempted command:

```text
docker compose build migrations
```

Result: not completed in the local environment.

Observed error after escalation:

```text
error during connect: Head "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/_ping": open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

Interpretation: Docker Desktop's Linux engine was not available locally. The Docker build should be validated on the AWS host with Docker running.

## Security Validation

* PostgreSQL remains internal to the Docker network.
* No PostgreSQL host port was added.
* The migration service publishes no ports.
* No secrets were hardcoded.
* Migration execution uses environment-provided `DATABASE_URL`.

## Result

The migration execution foundation is implemented.

AWS validation should now run:

```bash
docker compose build
docker compose run --rm migrations alembic upgrade head
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```

If the migration command succeeds, the database should no longer remain empty after container health validation.
