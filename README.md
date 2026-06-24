# Lead Generator App

Phase 0 repository scaffold for the Lead Generator App.

## Services

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + Alembic
- Worker: Python async service scaffold
- Database: PostgreSQL

## Local Startup

Copy `.env.example` to `.env`, fill all placeholder values, then run:

```bash
docker compose up -d
```

Health checks:

- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
