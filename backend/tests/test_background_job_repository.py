import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.models import BackgroundJob
from app.repositories.background_job_repository import BackgroundJobRepository
from app.schemas.background_job import empty_payload_envelope


def build_job(
    status: str = "pending",
    attempts: int = 0,
    locked_by: str | None = None,
) -> BackgroundJob:
    now = datetime.now(timezone.utc)
    return BackgroundJob(
        id=uuid4(),
        job_type="contact_collection",
        status=status,
        payload=empty_payload_envelope(
            request_id="request-1",
            idempotency_key=f"contact_collection:{uuid4()}:business_contact_pages",
            data={"business_id": str(uuid4())},
        ),
        attempts=attempts,
        max_attempts=3,
        locked_at=now if locked_by else None,
        locked_by=locked_by,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


class FakeScalarResult:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items


class FakeExecuteResult:
    def __init__(self, job):
        self.job = job

    def scalar_one_or_none(self):
        return self.job


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.flushed = False
        self.rolled_back = False
        self.active_duplicate = None
        self.objects = {}
        self.claim_job = None
        self.executed_statement = None
        self.executed_params = None

    def add(self, instance):
        if instance.id is None:
            instance.id = uuid4()
        now = datetime.now(timezone.utc)
        if instance.created_at is None:
            instance.created_at = now
        if instance.updated_at is None:
            instance.updated_at = now
        self.added.append(instance)
        self.objects[instance.id] = instance

    async def flush(self):
        self.flushed = True

    async def rollback(self):
        self.rolled_back = True

    async def scalar(self, statement):
        return self.active_duplicate

    async def scalars(self, statement):
        return FakeScalarResult([])

    async def get(self, model, id):
        return self.objects.get(id)

    async def execute(self, statement, params=None):
        self.executed_statement = str(statement)
        self.executed_params = params or {}
        if self.claim_job is not None:
            self.claim_job.status = "running"
            self.claim_job.locked_by = self.executed_params["worker_id"]
            self.claim_job.locked_at = datetime.now(timezone.utc)
            self.claim_job.attempts += 1
        return FakeExecuteResult(self.claim_job)


def test_create_job_returns_existing_active_duplicate() -> None:
    session = FakeSession()
    duplicate = build_job(status="pending")
    session.active_duplicate = duplicate
    repository = BackgroundJobRepository(session)

    result = asyncio.run(
        repository.create_job(
            "contact_collection",
            duplicate.payload,
            max_attempts=3,
        )
    )

    assert result is duplicate
    assert session.added == []


def test_create_job_adds_valid_payload_envelope() -> None:
    session = FakeSession()
    repository = BackgroundJobRepository(session)
    payload = empty_payload_envelope(
        request_id="request-2",
        idempotency_key="expired_refresh_token_cleanup:daily",
        data={"retention_days": 90},
    )

    result = asyncio.run(repository.create_job("expired_refresh_token_cleanup", payload))

    assert result.status == "pending"
    assert result.payload["schema_version"] == 1
    assert result.payload["idempotency_key"] == "expired_refresh_token_cleanup:daily"
    assert session.flushed is True


def test_claim_next_uses_postgresql_skip_locked_and_claims_once() -> None:
    session = FakeSession()
    session.claim_job = build_job(status="pending", attempts=0)
    repository = BackgroundJobRepository(session)

    result = asyncio.run(repository.claim_next("worker-1"))

    assert result is session.claim_job
    assert "FOR UPDATE SKIP LOCKED" in session.executed_statement
    assert result.status == "running"
    assert result.locked_by == "worker-1"
    assert result.attempts == 1


def test_complete_job_clears_lock_metadata() -> None:
    session = FakeSession()
    job = build_job(status="running", attempts=1, locked_by="worker-1")
    session.objects[job.id] = job
    repository = BackgroundJobRepository(session)

    result = asyncio.run(repository.complete_job(job.id, "worker-1"))

    assert result.status == "completed"
    assert result.locked_at is None
    assert result.locked_by is None
    assert result.error_message is None


def test_complete_job_rejects_job_locked_by_another_worker() -> None:
    session = FakeSession()
    job = build_job(status="running", attempts=1, locked_by="worker-1")
    session.objects[job.id] = job
    repository = BackgroundJobRepository(session)

    with pytest.raises(ConflictError):
        asyncio.run(repository.complete_job(job.id, "worker-2"))


def test_fail_job_schedules_retry_before_max_attempts() -> None:
    session = FakeSession()
    job = build_job(status="running", attempts=1, locked_by="worker-1")
    session.objects[job.id] = job
    repository = BackgroundJobRepository(session)

    result = asyncio.run(
        repository.fail_job(
            job.id,
            worker_id="worker-1",
            error_code="NETWORK_TIMEOUT",
            error_message="network timed out",
            retryable=True,
            retry_delay_seconds=30,
        )
    )

    assert result.status == "pending"
    assert result.locked_at is None
    assert result.locked_by is None
    assert result.payload["dead_letter"] is False
    assert result.payload["retry_after"] is not None
    assert result.payload["last_error_code"] == "NETWORK_TIMEOUT"


def test_fail_job_dead_letters_at_max_attempts() -> None:
    session = FakeSession()
    job = build_job(status="running", attempts=3, locked_by="worker-1")
    session.objects[job.id] = job
    repository = BackgroundJobRepository(session)

    result = asyncio.run(
        repository.fail_job(
            job.id,
            worker_id="worker-1",
            error_code="NETWORK_TIMEOUT",
            error_message="network timed out",
            retryable=True,
        )
    )

    assert result.status == "failed"
    assert result.payload["dead_letter"] is True
    assert result.payload["dead_letter_reason"] == "NETWORK_TIMEOUT"
    assert result.payload["retry_after"] is None
