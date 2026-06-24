# Phase 2D Auth Audit Hardening Report

Project: Lead Generator App

Repository: lead-generator-app

## Scope

Phase 2D implemented audit hardening only for the existing authentication and authorization system.

No business search, lead acquisition, contact collection, enrichment, scoring, export, crawler, or frontend business functionality was modified.

## Files Modified

### backend/app/core/exceptions.py

* Added a safe `failure_reason` attribute to `CsrfError`.
* Preserved the existing `CSRF_VALIDATION_FAILED` API error code and HTTP 403 behavior.

### backend/app/core/security.py

* Updated CSRF validation failures to classify safe failure reasons:
  * `missing_csrf_token`
  * `csrf_token_mismatch`
  * `invalid_csrf_token_format`
  * `invalid_csrf_token_signature`
* No CSRF token values are logged or exposed.

### backend/app/core/dependencies.py

* Updated `validate_csrf` to write an audit log entry before re-raising CSRF failures.
* CSRF failure audit entries include:
  * `event_type`
  * `user_id` when resolvable from the refresh token hash
  * `request_id`
  * IP address
  * timestamp through the `audit_logs.created_at` column
  * `failure_reason`
* Updated RBAC dependency handling to write audit log entries before re-raising authorization failures.
* Added `require_permissions` dependency for permission-based RBAC enforcement using the existing permission map.
* Permission denial audit entries include:
  * `event_type`
  * `user_id`
  * `required_permission`
  * `endpoint`
  * `request_id`
  * IP address
  * timestamp through the `audit_logs.created_at` column

### backend/app/services/auth_service.py

* Added `audit_csrf_failure`.
* Added `audit_permission_denied`.
* Added `get_user_id_for_refresh_token`, which resolves the user from a hashed refresh token lookup only.
* Raw refresh tokens are not stored, logged, or written to audit metadata.

### backend/tests/test_csrf.py

* Added test coverage verifying CSRF validation failure logging.
* The test asserts request id, IP address, known user field, and failure reason are captured.

### backend/tests/test_auth_me.py

* Added test coverage verifying permission denial logging.
* The test asserts user id, request id, IP address, required permission, and endpoint are captured.

## Files Created

### docs/phase-2-auth-audit-hardening-report.md

This report documents Phase 2D changes and verification status.

## Security Notes

* CSRF failure audit metadata records only safe failure reasons.
* Permission denial audit metadata records only endpoint and required permission.
* Token values, passwords, secrets, and raw refresh tokens are not logged.
* Refresh-token identity lookup uses the existing SHA-256 token hash lookup.
* Existing API error codes and response behavior are preserved.

## Tests Added

* `backend/tests/test_csrf.py::test_state_changing_auth_endpoint_requires_csrf_header`
* `backend/tests/test_auth_me.py::test_permission_denial_is_audited`

## Verification Performed

### Compile Check

Command:

```text
python -m compileall backend\app backend\tests
```

Result:

```text
Passed
```

### Focused Pytest

Command:

```text
python -m pytest backend\tests\test_csrf.py backend\tests\test_auth_me.py
```

Result:

```text
Timed out in the local host Python environment.
```

Additional dependency checks showed the host Python environment is not the project runtime:

```text
Python 3.10.9
ModuleNotFoundError: No module named 'fastapi'
```

### Docker Availability

Command:

```text
docker compose ps
```

Result:

```text
Docker was not reachable from this session.
The Docker client reported access denied for C:\Users\tijan\.docker\config.json and could not connect to the Docker engine pipe.
```

### Ruff

Command:

```text
python -m ruff check backend\app\core\dependencies.py backend\app\core\exceptions.py backend\app\core\security.py backend\app\services\auth_service.py backend\tests\test_csrf.py backend\tests\test_auth_me.py
```

Result:

```text
Not executed successfully because Ruff is not installed in the host Python environment.
```

### Black

Command:

```text
python -m black --check backend\app\core\dependencies.py backend\app\core\exceptions.py backend\app\core\security.py backend\app\services\auth_service.py backend\tests\test_csrf.py backend\tests\test_auth_me.py
```

Result:

```text
Not executed successfully because the host Black version does not support the project `py312` target.
```

## Limitations

* Runtime tests should be executed inside the approved project container or a Python 3.12 environment with `backend/requirements.txt` installed.
* Local host verification was limited to syntax compilation because the host environment is Python 3.10.9 and lacks FastAPI.

## Remaining Follow-Up Recommendations

* Run the focused authentication test files inside the backend container.
* Run the full backend test suite inside the backend container after dependencies are available.
