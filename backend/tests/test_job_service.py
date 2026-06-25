import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.background_job import (
    InternalJobCreateRequest,
    InternalJobStatusResponse,
    empty_payload_envelope,
)
from app.services.job_service import JobService


def build_job(status: str = "pending"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        job_type="contact_collection",
        status=status,
        attempts=0,
        max_attempts=3,
        payload=empty_payload_envelope(
            request_id="request-1",
            idempotency_key="contact_collection:business:mode",
            data={},
        ),
        locked_at=None,
        locked_by=None,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.refresh_count = 0

    async def commit(self):
        self.committed = True

    async def refresh(self, instance):
        self.refresh_count += 1
        instance.updated_at = datetime.now(timezone.utc)


class FakeJobRepository:
    def __init__(self) -> None:
        self.job = build_job()

    async def create_job(self, job_type, payload, max_attempts):
        self.job.job_type = job_type
        self.job.payload = payload
        self.job.max_attempts = max_attempts
        return self.job

    async def claim_next(self, worker_id):
        self.job.status = "running"
        self.job.locked_by = worker_id
        self.job.attempts = 1
        return self.job

    async def complete_job(self, job_id, worker_id):
        self.job.id = job_id
        self.job.status = "completed"
        return self.job


class FakeAuditRepository:
    def __init__(self) -> None:
        self.events = []

    async def log_event(self, event_type, request_id, user_id=None, ip_address=None, metadata=None):
        self.events.append(
            {
                "event_type": event_type,
                "request_id": request_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "metadata": metadata,
            }
        )


def build_service() -> tuple[JobService, FakeSession, FakeAuditRepository]:
    service = JobService.__new__(JobService)
    session = FakeSession()
    audit_logs = FakeAuditRepository()
    service.session = session
    service.jobs = FakeJobRepository()
    service.audit_logs = audit_logs
    return service, session, audit_logs


def test_job_service_refreshes_create_claim_complete_before_serialization() -> None:
    service, session, audit_logs = build_service()
    context = SimpleNamespace(request_id="request-1", ip_address="127.0.0.1")
    payload = InternalJobCreateRequest(
        job_type="contact_collection",
        idempotency_key="contact_collection:business:mode",
        data={},
    )

    created = asyncio.run(service.create_job(payload, context))
    claimed = asyncio.run(service.claim_next_job("worker-1", context))
    completed = asyncio.run(service.complete_job(created.id, "worker-1", context))

    assert created.id == claimed.id == completed.id
    assert session.committed is True
    assert session.refresh_count == 3
    serialized = InternalJobStatusResponse.from_job(completed).model_dump(mode="json")
    assert serialized["status"] == "completed"
    assert serialized["updated_at"] is not None
    assert [event["event_type"] for event in audit_logs.events] == [
        "background_job_created",
        "background_job_claimed",
        "background_job_completed",
    ]
    assert audit_logs.events[0]["metadata"]["job_id"] == str(created.id)
    assert audit_logs.events[1]["metadata"]["worker_id"] == "worker-1"
