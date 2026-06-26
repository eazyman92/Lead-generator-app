# Phase 5A Frontend Search Dashboard

## Scope

Phase 5A replaces the placeholder frontend with an authenticated production
search dashboard for the Lead Generator App.

Implemented:

* cookie-based login using `POST /api/v1/auth/login`
* authenticated dashboard guard using `GET /api/v1/auth/me`
* CSRF-aware API client using the existing `csrf_token` cookie and `X-CSRF-Token` header
* business search form using the existing `POST /api/v1/search` schema
* Zod validation and React Hook Form
* paginated business results table
* toast notifications
* skeleton loading states
* dark-mode-first dashboard shell
* job status indicator using existing job metadata and internal job status contracts

## API Usage

The frontend uses existing backend APIs only:

* `GET /api/v1/auth/csrf`
* `POST /api/v1/auth/login`
* `POST /api/v1/auth/logout`
* `POST /api/v1/auth/refresh`
* `GET /api/v1/auth/me`
* `POST /api/v1/search`

The dashboard reads job status through a Next.js server route that proxies the
existing backend internal endpoint:

* `GET /internal/v1/jobs/{job_id}`

`INTERNAL_API_TOKEN` is used only on the server side and must not be exposed as
a `NEXT_PUBLIC_*` variable.

## Search Payload

```json
{
  "filters": {
    "industry": "Restaurants",
    "country": "Nigeria",
    "state": "Lagos",
    "city": "Ikeja"
  },
  "pagination": {
    "page": 1,
    "per_page": 20
  }
}
```

## Validation

Local commands:

```bash
npm install
npm run lint
npm run build
npm test
docker compose build frontend
docker compose up -d
```

AWS validation should confirm:

* frontend container is healthy
* login succeeds with existing backend auth
* dashboard redirects unauthenticated users to `/login`
* search submits to `/api/v1/search`
* businesses render in the results table
* contact collection job status progresses when `INTERNAL_API_TOKEN` is configured
