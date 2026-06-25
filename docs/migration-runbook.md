# Migration Runbook

Project: Lead Generator App

## Purpose

Provide repeatable commands for building the Docker stack, running Alembic migrations, and verifying PostgreSQL schema state.

## Preconditions

* Docker and Docker Compose are installed.
* A `.env` file exists and follows `.env.example`.
* `DATABASE_URL` points to the Compose PostgreSQL service host named `postgres`.
* PostgreSQL is not exposed through a public host port.

## 1. Build Images

```bash
docker compose build
```

Expected result:

* frontend image builds
* backend image builds
* worker image builds
* migrations service image builds from the backend Dockerfile

## 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

Verify PostgreSQL health:

```bash
docker compose ps postgres
```

Expected result:

* PostgreSQL status is healthy

## 3. Run Migrations

```bash
docker compose run --rm migrations alembic upgrade head
```

Expected result:

* Alembic reads `/app/alembic.ini`
* Alembic loads `/app/database/migrations`
* Alembic connects using `DATABASE_URL`
* Alembic applies all revisions through `head`
* command exits with status `0`

## 4. Verify Tables

Open psql inside the PostgreSQL container:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

List tables:

```sql
\dt
```

One-command table check:

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

## 5. Verify Current Alembic Revision

```bash
docker compose run --rm migrations alembic current
```

Expected result:

* current revision matches the latest migration head

## 6. Start Application Services

```bash
docker compose up -d
```

Expected result:

* migrations complete successfully
* backend becomes healthy
* worker becomes healthy
* frontend becomes healthy

## 7. Troubleshooting

### `alembic.ini` Not Found

Rebuild the backend image:

```bash
docker compose build backend migrations
```

Then rerun:

```bash
docker compose run --rm migrations alembic upgrade head
```

### `database/migrations` Not Found

Confirm the backend image was built from the repository root using `backend/Dockerfile`.

Expected Compose configuration:

```yaml
build:
  context: .
  dockerfile: backend/Dockerfile
```

### Database Has No Tables

Run:

```bash
docker compose run --rm migrations alembic upgrade head
```

Then verify:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```

### PostgreSQL Connection Failure

Verify:

* PostgreSQL container is healthy
* `DATABASE_URL` uses host `postgres`
* database name, user, and password match `.env`
* no public PostgreSQL port is required

## Safety Notes

* Do not run migrations from the worker service.
* Do not expose PostgreSQL publicly.
* Do not hardcode credentials in Compose files or documentation.
* Investigate failed migrations before continuing deployment.
