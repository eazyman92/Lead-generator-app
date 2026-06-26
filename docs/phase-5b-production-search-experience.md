# Phase 5B Production Search Experience

## Summary

Phase 5B upgrades the dashboard search experience without changing public API
contracts.

Implemented:

* production dashboard copy and Lead Generator App branding
* disabled unfinished sidebar items
* account menu with session details and sign out
* searchable dropdowns for industry, country, state, and city
* ISO-style country dataset with country codes
* state options scoped to the selected country
* city options scoped to the selected state
* automatic refresh of persisted business results after a contact collection job completes
* regression tests for dropdown selection, cascading geography, and completed-job result refresh

## Search Flow

1. User submits `POST /api/v1/search`.
2. Backend returns persisted matches when available.
3. If no persisted businesses exist for the filters, backend creates a
   `contact_collection` job and returns the job id.
4. Frontend polls existing job status through the existing Next.js server route.
5. When the job reaches `completed`, the frontend re-queries the existing
   `POST /api/v1/search` endpoint.
6. Backend returns businesses saved by the worker and does not enqueue a
   duplicate job for a completed idempotency key.
7. Results table renders worker-persisted business name, phone, email, website,
   address, and source.

## API Compatibility

No new public API endpoints were introduced.

The existing endpoint remains the source of truth:

```text
POST /api/v1/search
```

The existing internal job status proxy remains unchanged:

```text
GET /api/job-status/{jobId}
```

## Validation

Recommended commands:

```bash
cd frontend
npm run type-check
npm test
npm run lint
npm run build

cd ..
python -m pytest backend/tests/test_search_service.py -q
docker compose build frontend backend
docker compose up -d
```

AWS browser validation:

1. Sign in or create an account.
2. Confirm only the Search sidebar item is enabled.
3. Select country, state, and city with the searchable dropdowns.
4. Submit a search that creates a `contact_collection` job.
5. Wait for the job status to complete.
6. Confirm the table refreshes with worker-saved businesses instead of the
   initial empty response.
