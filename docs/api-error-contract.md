# API Error Contract (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines the standard API response and error format.

All public APIs under `/api/v1/*` and internal APIs under `/internal/v1/*` must follow this contract.

---

# 2. Success Response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "request_id": "..."
}
```

---

# 3. Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message."
  },
  "request_id": "..."
}
```

---

# 4. Error Rules

Error responses must never expose:

* stack traces
* raw database errors
* secrets
* tokens
* internal file paths

Every error response must include `request_id`.

---

# 5. Common HTTP Status Codes

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests
500 Internal Server Error
```

---

# 6. Validation Errors

Validation errors should use HTTP `422` and the standard response envelope.

Field-level details may be included inside `error.details` when safe:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed.",
    "details": {
      "fields": {
        "email": "Invalid email format."
      }
    }
  },
  "request_id": "..."
}
```
