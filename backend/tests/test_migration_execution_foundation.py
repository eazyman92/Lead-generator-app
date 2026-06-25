from pathlib import Path


def test_backend_image_includes_alembic_assets() -> None:
    dockerfile = Path("backend/Dockerfile").read_text(encoding="utf-8")

    assert "COPY backend/requirements.txt ." in dockerfile
    assert "COPY backend/app ./app" in dockerfile
    assert "COPY alembic.ini ./alembic.ini" in dockerfile
    assert "COPY database/migrations ./database/migrations" in dockerfile


def test_compose_defines_dedicated_migration_service() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "migrations:" in compose
    assert "dockerfile: backend/Dockerfile" in compose
    assert "DATABASE_URL: ${DATABASE_URL}" in compose
    assert 'command: ["alembic", "upgrade", "head"]' in compose
    assert "condition: service_completed_successfully" in compose


def test_alembic_env_uses_async_database_url_driver() -> None:
    env_py = Path("database/migrations/env.py").read_text(encoding="utf-8")

    assert "from sqlalchemy.ext.asyncio import async_engine_from_config" in env_py
    assert "return database_url" in env_py
    assert "replace(\"+asyncpg\", \"\")" not in env_py
    assert "await connection.run_sync(do_run_migrations)" in env_py
