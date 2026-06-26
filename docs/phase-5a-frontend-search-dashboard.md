# Phase 5A Frontend Search Dashboard

## Scope

Phase 5A replaces the placeholder frontend with an authenticated production
search dashboard for the Lead Generator App.

Implemented:

* same-origin frontend API proxy for browser-safe `/api/v1/*` requests
* cookie-based login using `POST /api/v1/auth/login`
* first-user account creation using `POST /api/v1/auth/register`
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
* `POST /api/v1/auth/register`
* `POST /api/v1/auth/login`
* `POST /api/v1/auth/logout`
* `POST /api/v1/auth/refresh`
* `GET /api/v1/auth/me`
* `POST /api/v1/search`

Browser-side API calls use same-origin relative URLs such as
`/api/v1/auth/csrf`. The Next.js frontend proxies those requests to the backend
using `BACKEND_INTERNAL_BASE_URL`, which should resolve to `http://backend:8000`
inside Docker Compose. `NEXT_PUBLIC_API_BASE_URL` is optional and should remain
empty for the standard Docker deployment so browsers do not call
`localhost:8000` from the user's machine.

The dashboard reads job status through a Next.js server route that proxies the
existing backend internal endpoint:

* `GET /internal/v1/jobs/{job_id}`

`INTERNAL_API_TOKEN` is used only on the server side and must not be exposed as
a `NEXT_PUBLIC_*` variable.

## Authentication Bootstrap

The first user is created through the existing registration endpoint exposed on
the login page. The flow is:

1. Browser requests `GET /api/v1/auth/csrf` through the Next.js proxy.
2. Backend sets the readable `csrf_token` cookie.
3. Browser submits `POST /api/v1/auth/register` with `X-CSRF-Token`.
4. Backend sets HTTP-only access and refresh token cookies.
5. Frontend redirects to the dashboard.

For AWS deployments, leave `AUTH_COOKIE_DOMAIN` empty unless a real shared
domain is intentionally configured. Empty domain values create host-only cookies
for the public frontend origin.

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
* browser devtools show auth requests going to `/api/v1/*` on the frontend origin
* account creation succeeds through the existing registration endpoint
* login succeeds with existing backend auth
* dashboard redirects unauthenticated users to `/login`
* search submits to `/api/v1/search`
* businesses render in the results table
* contact collection job status progresses when `INTERNAL_API_TOKEN` is configured
