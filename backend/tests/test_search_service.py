import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.schemas.search import BusinessSearchRequest, PaginationRequest
from app.services.search_service import SearchService


@dataclass
class FakeUser:
    id: UUID
    role: str = "user"


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeBusinessRepository:
    def __init__(self, total: int = 2) -> None:
        self.total = total
        self.search_calls = []

    async def count_search(self, industry, country, state, city):
        return self.total

    async def search(self, industry, country, state, city, limit, offset):
        self.search_calls.append(
            {
                "industry": industry,
                "country": country,
                "state": state,
                "city": city,
                "limit": limit,
                "offset": offset,
            }
        )
        return []


class FakeSearchLogRepository:
    def __init__(self) -> None:
        self.created = []

    async def create(self, values):
        self.created.append(values)


class FakeAuditLogRepository:
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


class FakeBackgroundJobRepository:
    def __init__(self, latest_status=None) -> None:
        self.created = []
        self.latest_status = latest_status

    async def get_latest_by_idempotency_key(self, job_type, idempotency_key):
        if self.latest_status is None:
            return None
        return SimpleNamespace(status=self.latest_status)

    async def create_job(self, job_type, payload, max_attempts=3):
        self.created.append(
            {
                "job_type": job_type,
                "payload": payload,
                "max_attempts": max_attempts,
            }
        )
        return SimpleNamespace(id=uuid4(), job_type=job_type)


def test_search_service_returns_persisted_results_without_queueing_duplicate_job() -> None:
    service = SearchService.__new__(SearchService)
    service.session = FakeSession()
    service.businesses = FakeBusinessRepository()
    service.search_logs = FakeSearchLogRepository()
    service.background_jobs = FakeBackgroundJobRepository()
    service.audit_logs = FakeAuditLogRepository()
    user = FakeUser(id=uuid4())
    context = SimpleNamespace(request_id="request-1", ip_address="127.0.0.1")
    payload = BusinessSearchRequest(
        filters={
            "industry": " Gym ",
            "country": " United States ",
            "state": " Texas ",
            "city": " Houston ",
        },
        pagination={"page": 2, "per_page": 10},
    )

    result = asyncio.run(service.search(payload, user, context))

    assert service.businesses.search_calls == [
        {
            "industry": "Gym",
            "country": "United States",
            "state": "Texas",
            "city": "Houston",
            "limit": 10,
            "offset": 10,
        }
    ]
    assert service.search_logs.created == [
        {
            "user_id": user.id,
            "request_id": "request-1",
            "industry": "Gym",
            "country": "United States",
            "state": "Texas",
            "city": "Houston",
            "results_count": 2,
        }
    ]
    assert service.background_jobs.created == []
    assert service.audit_logs.events[0]["event_type"] == "business_search"
    assert service.audit_logs.events[0]["user_id"] == user.id
    assert service.audit_logs.events[0]["metadata"]["results_count"] == 2
    assert result.job_id is None
    assert result.pagination.page == 2
    assert service.session.committed is True


def test_search_service_queues_collection_when_no_persisted_results_exist() -> None:
    service = SearchService.__new__(SearchService)
    service.session = FakeSession()
    service.businesses = FakeBusinessRepository(total=0)
    service.search_logs = FakeSearchLogRepository()
    service.background_jobs = FakeBackgroundJobRepository()
    service.audit_logs = FakeAuditLogRepository()
    user = FakeUser(id=uuid4())
    context = SimpleNamespace(request_id="request-1", ip_address="127.0.0.1")
    payload = BusinessSearchRequest(
        filters={
            "industry": " Gym ",
            "country": " United States ",
            "state": " Texas ",
            "city": " Houston ",
        },
        pagination={"page": 2, "per_page": 10},
    )

    result = asyncio.run(service.search(payload, user, context))

    assert service.background_jobs.created[0]["job_type"] == "contact_collection"
    job_payload = service.background_jobs.created[0]["payload"]
    assert job_payload["data"]["query"] == "Gym"
    assert job_payload["data"]["location"] == "Houston, Texas, United States"
    assert job_payload["data"]["country"] == "United States"
    assert job_payload["data"]["state"] == "Texas"
    assert job_payload["data"]["city"] == "Houston"
    assert job_payload["data"]["limit"] == 10
    assert job_payload["data"]["user_id"] == str(user.id)
    assert job_payload["data"]["idempotency_key"] == job_payload["idempotency_key"]
    assert service.audit_logs.events[1]["event_type"] == "background_job_created"
    assert result.job_id is not None
    assert result.pagination.page == 2
    assert service.session.committed is True


def test_search_service_requeues_when_only_stale_completed_empty_collection_exists() -> None:
    service = SearchService.__new__(SearchService)
    service.session = FakeSession()
    service.businesses = FakeBusinessRepository(total=0)
    service.search_logs = FakeSearchLogRepository()
    service.background_jobs = FakeBackgroundJobRepository(latest_status="completed")
    service.audit_logs = FakeAuditLogRepository()
    user = FakeUser(id=uuid4())
    context = SimpleNamespace(request_id="request-3", ip_address="127.0.0.1")
    payload = BusinessSearchRequest(
        filters={
            "industry": "Restaurants",
            "country": "Nigeria",
            "state": "Lagos",
            "city": "Ikeja",
        }
    )

    result = asyncio.run(service.search(payload, user, context))

    assert service.background_jobs.created[0]["job_type"] == "contact_collection"
    assert result.job_id is not None
    assert result.pagination.total == 0


def test_search_history_audits_view() -> None:
    service = SearchService.__new__(SearchService)
    service.session = FakeSession()
    service.audit_logs = FakeAuditLogRepository()

    class FakeHistoryRepository:
        async def count_history(self, user_id):
            assert user_id == user.id
            return 0

        async def list_history(self, user_id, limit, offset):
            assert user_id == user.id
            return []

    service.search_logs = FakeHistoryRepository()
    user = FakeUser(id=uuid4())
    context = SimpleNamespace(request_id="request-2", ip_address="127.0.0.1")

    result = asyncio.run(service.history(PaginationRequest(), user, context))

    assert result.history == []
    assert service.audit_logs.events[0]["event_type"] == "search_history_viewed"
    assert service.audit_logs.events[0]["user_id"] == user.id
    assert service.session.committed is True
