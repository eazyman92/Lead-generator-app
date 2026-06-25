# Database Migration Strategy

Project: Lead Generator App

## Purpose

Define the long-term strategy for executing PostgreSQL schema migrations in Docker Compose environments.

## Selected Strategy

The project uses a dedicated Docker Compose migration service named `migrations`.

The migration service:

* uses the backend image
* includes `alembic.ini`
* includes `database/migrations`
* includes backend application models under `backend/app`
* runs `alembic upgrade head`
* connects to PostgreSQL through the internal Docker network
* exits after migrations complete

## Rationale

This strategy keeps schema changes explicit and operationally visible.

It avoids:

* hidden schema changes during backend application startup
* coupling API process health to migration execution
* requiring the worker image to contain migration tooling
* exposing PostgreSQL publicly

The backend and worker services remain application runtime services. The migration service owns database schema initialization and upgrades.

## Rejected Approaches

### Backend Startup Migration

Rejected as the default long-term strategy.

Reasons:

* every backend replica could attempt migration execution
* API startup side effects are harder to reason about
* failed migrations can obscure application health checks
* migration execution should be deliberate in deployment workflows

### Worker Startup Migration

Rejected.

Reasons:

* workers should not own schema lifecycle
* future worker scaling could create multiple migration runners
* migration tooling belongs with backend models and Alembic configuration

### Manual Host Execution Only

Rejected as the only strategy.

Reasons:

* host environments may not have the correct Python dependencies
* containerized migration execution better matches deployment runtime
* Compose-based validation is easier to repeat across development and AWS

## Runtime Assets

The backend image must contain:

* `/app/app`
* `/app/alembic.ini`
* `/app/database/migrations`

The migration service uses these files directly.

## Database URL

Migrations use the existing `DATABASE_URL` environment variable.

The project standard URL uses SQLAlchemy asyncpg format:

```text
postgresql+asyncpg://<user>:<password>@postgres:5432/<database>
```

Alembic runs migrations through SQLAlchemy's async engine so no separate synchronous PostgreSQL driver is required.

## Docker Compose Behavior

The `migrations` service depends on healthy PostgreSQL.

The backend service depends on:

* healthy PostgreSQL
* successful completion of the `migrations` service

The migration service must not publish ports.

PostgreSQL remains internal to the Docker network and is not publicly exposed.

## Standard Commands

Build images:

```bash
docker compose build
```

Run migrations:

```bash
docker compose run --rm migrations alembic upgrade head
```

Start the stack:

```bash
docker compose up -d
```

Verify tables:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```

## Operational Rules

* Run migrations before validating backend features that depend on database tables.
* Do not run migrations from the worker container.
* Do not expose PostgreSQL host ports for migration execution.
* Do not store database credentials in documentation or source files.
* Use `.env` values derived from `.env.example`.
* Failed migrations must be investigated before starting new application phases.
