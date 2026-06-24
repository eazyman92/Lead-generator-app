# Coding Standards

## Project

Lead Generator App

---

# 1. Purpose

This document defines coding standards for:

- frontend
- backend
- workers
- infrastructure

All generated code must comply.

---

# 2. General Principles

Code must be:

- readable
- secure
- maintainable
- testable
- documented

Code clarity is preferred over cleverness.

---

# 3. Security Rules

Mandatory:

- No hardcoded secrets
- No API keys in source code
- No credentials in repositories
- Environment variables only
- Authentication tokens must use HTTP-only secure cookies

Forbidden:

- plaintext passwords
- embedded tokens
- embedded connection strings
- token storage in localStorage
- token storage in sessionStorage
- token exposure through browser-accessible JavaScript variables

---

# 4. Naming Conventions

## Files

snake_case

Examples:

user_service.py
search_engine.py

---

## Classes

PascalCase

Examples:

UserService
SearchEngine

---

## Functions

snake_case

Examples:

create_user()
search_businesses()

---

## Constants

UPPER_CASE

Examples:

MAX_RESULTS
DEFAULT_TIMEOUT

---

# 5. Python Standards

Version:

Python 3.12+

Requirements:

- type hints mandatory
- docstrings mandatory
- async where appropriate

Example:

async def search_businesses(
    industry: str
) -> list[Business]:
    """Search businesses by industry."""

# 6. FastAPI Standards

- Pydantic validation required
- No raw SQL in routes
- Business logic separated from controllers

Folder Pattern:

backend/app/api/
backend/app/services/
backend/app/repositories/
backend/app/models/
backend/app/schemas/

---

# 7. Frontend Standards

Next.js App Router

TypeScript strict mode

Requirements:

- no any types
- reusable components
- server components preferred

---

# 8. Database Standards

PostgreSQL

Requirements:

- UUID primary keys
- indexed search fields
- migrations via Alembic

No direct schema changes.

---

# 9. Logging Standards

Use structured logging.

Never log:

- passwords
- tokens
- secrets

---

# 10. Testing Standards

Minimum:

- unit tests
- integration tests

Coverage target:

80%+

