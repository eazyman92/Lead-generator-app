# Job Queue Specification (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines the V1 background job system.

V1 uses PostgreSQL-backed jobs and polling workers. No external queue is required.

---

# 2. Approved Technology

Use:

* PostgreSQL
* SQLAlchemy
* Python async worker services

Do not introduce Redis, Celery, or another queue system in V1.

---

# 3. Job Table

The job table is:

```sql
background_jobs
```

Required fields are defined in `data-model.md`.

---

# 4. Job Statuses

Allowed statuses:

```text
pending
running
completed
failed
```

---

# 5. Worker Behavior

Workers must:

* poll for `pending` jobs
* lock a job before execution
* update status to `running`
* update status to `completed` on success
* update attempts and error_message on failure
* stop retrying after max_attempts

Workers must use `request_id` when triggered by an API request.

---

# 6. Internal API Routes

Internal worker routes use:

```text
/internal/v1/*
```

Internal routes must:

* never be publicly exposed
* require `INTERNAL_API_TOKEN`
* be available only on the private Docker network

---

# 7. MVP Job Types

Required MVP job types:

```text
contact_collection
csv_export
expired_refresh_token_cleanup
```

Future job types:

```text
decision_maker_enrichment
opportunity_scoring
advanced_intelligence
```
