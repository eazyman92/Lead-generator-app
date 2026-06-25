# Phase 4A Step 2 Implementation Report

Project: Lead Generator App

Date: 2026-06-25

Scope: Phase 4A Step 2 background job queue foundation plus the internal job-control endpoints explicitly requested for this implementation pass.

No contact collection, CSV export generation, enrichment, scoring, frontend pages, worker executor, crawler, or external acquisition behavior was implemented.

## Documentation Review And Ambiguities

Reviewed:

* `docs/phase-4a-implementation-plan.md`
* `docs/job-queue-design.md`
* `docs/background-job-spec.md`
* `docs/internal-api-contracts.md`
* `docs/api-spec.md`
* `docs/rbac-permissions-matrix.md`
* `docs/dead-letter-strategy.md`
* `docs/security-standards.md`

Ambiguities resolved for this implementation:

* `phase-4a-implementation-plan.md` labels internal APIs as Step 3, but this task explicitly required internal job endpoints in Step 2. Implemented only generic job-control internal endpoints required by this request: create, claim, complete, fail, and get status.
* Existing internal API docs define contact-collection, CSV-export, retry, and cancel endpoints, but this task prohibited implementing contact collection and CSV export. Those specific workflow endpoints were not implemented.
* `job-queue-design.md` says attempts increment during claim. The task says retry handling should increment attempts on failure. This implementation follows the documented queue design: attempts increment atomically when a job is claimed, so a failed job has already consumed the current attempt.

## Implemented

### Background Job Repository

Implemented:

* idempotent job creation using `job_type` plus `payload.idempotency_key`
* duplicate active job lookup for `pending` and `running`
* eligible pending job listing
* atomic PostgreSQL claim using `FOR UPDATE SKIP LOCKED`
* completion transition from `running` to `completed`
* failure transition from `running` to retryable `pending` or terminal `failed`
* dead-letter payload metadata
* lock ownership validation using `locked_by`
* sanitized error persistence

### Job Lifecycle

Supported statuses:

* `pending`
* `running`
* `completed`
* `failed`

Enforced transitions:

* `pending` to `running`
* `running` to `completed`
* `running` to retryable `pending`
* `running` to terminal `failed`
* `pending` to `failed`

Completed and failed jobs are not re-opened by repository lifecycle methods.

### Retry And Dead-Letter Handling

Retryable error codes:

* `NETWORK_TIMEOUT`
* `DNS_FAILURE`
* `HTTP_429`
* `HTTP_5XX`
* `DB_CONFLICT`

Retryable failures return the job to `pending` only when attempts remain.

Terminal failures set:

* `status = failed`
* `payload.dead_letter = true`
* `payload.dead_letter_reason`
* `payload.last_error_code`
* `payload.last_error_at`

### Internal APIs

Implemented:

* `POST /internal/v1/jobs`
* `POST /internal/v1/jobs/claim`
* `GET /internal/v1/jobs/{job_id}`
* `POST /internal/v1/jobs/{job_id}/complete`
* `POST /internal/v1/jobs/{job_id}/fail`

Security:

* requires `X-Internal-API-Token`
* requires `X-Request-ID`
* valid internal token resolves to `system_worker`
* endpoint-level internal permissions are enforced
* responses use the standard response wrapper
* errors use the existing `AppError` standard error wrapper

### Audit Logging

Implemented lifecycle audit events:

* `background_job_created`
* `background_job_claimed`
* `background_job_completed`
* `background_job_retry_scheduled`
* `background_job_dead_lettered`
* `background_job_failed`
* `background_job_status_viewed`

Audit metadata includes:

* `job_id`
* `job_type`
* `worker_id` where applicable
* retry/failure metadata where applicable

## Files Changed

Modified:

* `backend/app/core/dependencies.py`
* `backend/app/core/permissions.py`
* `backend/app/main.py`
* `backend/app/repositories/background_job_repository.py`
* `backend/app/schemas/background_job.py`

Created:

* `backend/app/api/internal.py`
* `backend/app/services/job_service.py`
* `backend/tests/test_background_job_repository.py`
* `backend/tests/test_internal_jobs_api.py`
* `backend/tests/test_job_service.py`
* `docs/phase-4a-step-2-implementation-report.md`

## Tests Added

Repository tests:

* idempotent duplicate active job returns existing job
* valid job creation uses the canonical payload envelope
* claim SQL uses `FOR UPDATE SKIP LOCKED`
* claim sets `running`, `locked_by`, and increments attempts
* completion clears lock metadata
* completion rejects jobs locked by another worker
* retryable failure schedules retry
* max-attempt failure dead-letters

API tests:

* missing internal token returns `INTERNAL_AUTH_REQUIRED`
* missing request id returns `REQUEST_ID_REQUIRED`
* create job returns standard response
* claim job returns claimed job
* complete endpoint works through service dependency
* fail endpoint works through service dependency
* get job status omits raw payload/data

Service tests:

* create, claim, and complete write lifecycle audit events

## Commands Executed

```text
python -m py_compile backend/app/repositories/background_job_repository.py backend/app/schemas/background_job.py backend/app/services/job_service.py backend/app/api/internal.py backend/app/core/dependencies.py backend/app/core/permissions.py backend/app/main.py backend/tests/test_background_job_repository.py backend/tests/test_internal_jobs_api.py backend/tests/test_job_service.py
```

Result: passed

```text
python -c "<line length check for touched files>"
```

Result: passed; no lines over 100 characters.

```text
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest backend/tests/test_migration_execution_foundation.py backend/tests/test_migration_definition.py -q
```

Result:

```text
10 passed
```

Attempted:

```text
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest backend/tests/test_background_job_repository.py backend/tests/test_internal_jobs_api.py backend/tests/test_job_service.py -q
```

Result: blocked in the host Python environment because installed local packages do not match the project runtime:

* local SQLAlchemy lacks `mapped_column`
* local FastAPI is not installed

Attempted Docker validation:

```text
docker compose build backend
```

Result: blocked by Docker Hub network timeout:

```text
python:3.12-slim: failed to resolve source metadata ... TLS handshake timeout
```

The Docker build was retried once and failed with the same external timeout.

## Validation Results

Static validation passed.

Existing migration/config tests passed.

Runtime test execution for the new job/API tests requires the backend project dependency set from `backend/requirements.txt` or a successfully built backend container.

## Known Blockers

Local runtime blockers only:

* Host Python environment does not contain the backend dependency stack.
* Docker build could not pull base image metadata because of Docker Hub TLS timeouts.

No implementation blocker was discovered in the Phase 4A Step 2 code path.

## Next Validation Command

Run in an environment with Docker Hub access or a cached backend image:

```bash
docker compose build backend
```

The backend runtime image does not copy tests by default. To run these tests inside that image, mount the backend tests directory:

```bash
docker compose run --rm -v "$PWD/backend/tests:/app/tests:ro" backend python -m pytest tests/test_background_job_repository.py tests/test_internal_jobs_api.py tests/test_job_service.py -q
```
