from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.internal import get_job_service
from app.main import app


def build_job(status: str = "pending"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        job_type="contact_collection",
        status=status,
        attempts=0,
        max_attempts=3,
        payload={
            "retry_after": None,
            "dead_letter": False,
            "dead_letter_reason": None,
            "cancelled": False,
            "cancelled_reason": None,
            "last_error_code": None,
            "last_error_at": None,
        },
        locked_at=None,
        locked_by=None,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


class FakeJobService:
    def __init__(self) -> None:
        self.created_payload = None
        self.claim_worker_id = None
        self.completed = None
        self.failed = None
        self.job = build_job()

    async def create_job(self, payload, context):
        self.created_payload = payload
        return self.job

    async def claim_next_job(self, worker_id, context):
        self.claim_worker_id = worker_id
        self.job.status = "running"
        self.job.locked_by = worker_id
        self.job.attempts = 1
        return self.job

    async def complete_job(self, job_id, worker_id, context):
        self.completed = {"job_id": job_id, "worker_id": worker_id}
        self.job.id = job_id
        self.job.status = "completed"
        return self.job

    async def fail_job(
        self,
        job_id,
        worker_id,
        error_code,
        error_message,
        retryable,
        retry_delay_seconds,
        context,
    ):
        self.failed = {
            "job_id": job_id,
            "worker_id": worker_id,
            "error_code": error_code,
            "retryable": retryable,
            "retry_delay_seconds": retry_delay_seconds,
        }
        self.job.id = job_id
        self.job.status = "pending" if retryable else "failed"
        self.job.payload["last_error_code"] = error_code
        return self.job

    async def get_job(self, job_id, context):
        self.job.id = job_id
        return self.job


def internal_headers(token: str = "test-internal-token") -> dict[str, str]:
    return {
        "X-Internal-API-Token": token,
        "X-Request-ID": "request-1",
    }


def test_internal_create_job_requires_internal_token() -> None:
    client = TestClient(app)

    response = client.post(
        "/internal/v1/jobs",
        headers={"X-Request-ID": "request-1"},
        json={
            "job_type": "contact_collection",
            "idempotency_key": "contact_collection:business:mode",
            "data": {},
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INTERNAL_AUTH_REQUIRED"


def test_internal_create_job_rejects_missing_request_id() -> None:
    client = TestClient(app)

    response = client.post(
        "/internal/v1/jobs",
        headers={"X-Internal-API-Token": "test-internal-token"},
        json={
            "job_type": "contact_collection",
            "idempotency_key": "contact_collection:business:mode",
            "data": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REQUEST_ID_REQUIRED"


def test_internal_create_job_returns_standard_response() -> None:
    service = FakeJobService()
    app.dependency_overrides[get_job_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/internal/v1/jobs",
        headers=internal_headers(),
        json={
            "job_type": "contact_collection",
            "idempotency_key": "contact_collection:business:mode",
            "data": {"business_id": str(uuid4())},
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["request_id"] == "request-1"
    assert body["data"]["job"]["job_type"] == "contact_collection"
    assert service.created_payload.idempotency_key == "contact_collection:business:mode"


def test_internal_claim_job_returns_claimed_job() -> None:
    service = FakeJobService()
    app.dependency_overrides[get_job_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/internal/v1/jobs/claim",
        headers=internal_headers(),
        json={"worker_id": "worker-1"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["job"]["status"] == "running"
    assert response.json()["data"]["job"]["locked_by"] == "worker-1"
    assert service.claim_worker_id == "worker-1"


def test_internal_complete_and_fail_job_endpoints() -> None:
    service = FakeJobService()
    app.dependency_overrides[get_job_service] = lambda: service
    client = TestClient(app)
    job_id = uuid4()

    complete_response = client.post(
        f"/internal/v1/jobs/{job_id}/complete",
        headers=internal_headers(),
        json={"worker_id": "worker-1"},
    )
    fail_response = client.post(
        f"/internal/v1/jobs/{job_id}/fail",
        headers=internal_headers(),
        json={
            "worker_id": "worker-1",
            "error_code": "NETWORK_TIMEOUT",
            "error_message": "timeout",
            "retryable": True,
            "retry_delay_seconds": 30,
        },
    )

    app.dependency_overrides.clear()

    assert complete_response.status_code == 200
    assert complete_response.json()["data"]["job"]["status"] == "completed"
    assert service.completed == {"job_id": job_id, "worker_id": "worker-1"}
    assert fail_response.status_code == 200
    assert fail_response.json()["data"]["job"]["status"] == "pending"
    assert service.failed["error_code"] == "NETWORK_TIMEOUT"


def test_internal_get_job_status_returns_sanitized_metadata() -> None:
    service = FakeJobService()
    app.dependency_overrides[get_job_service] = lambda: service
    client = TestClient(app)
    job_id = uuid4()

    response = client.get(f"/internal/v1/jobs/{job_id}", headers=internal_headers())

    app.dependency_overrides.clear()

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["id"] == str(job_id)
    assert "payload" not in job
    assert "data" not in job
