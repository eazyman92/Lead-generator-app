from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.businesses import get_business_service
from app.api.search import get_search_service
from app.core.dependencies import get_auth_service
from app.core.security import create_access_token, generate_csrf_token
from app.main import app
from app.schemas.search import PaginationResponse
from app.services.business_service import (
    BusinessContactsResult,
    BusinessDetailResult,
    BusinessSourcesResult,
)
from app.services.search_service import SearchHistoryResults, SearchResults


class SearchAuthService:
    def __init__(self, user) -> None:
        self.user = user

    async def get_active_user(self, user_id: UUID):
        assert user_id == self.user.id
        return self.user

    async def audit_permission_denied(self, user, context, required_permission, endpoint):
        raise AssertionError("permission should not be denied")

    async def get_user_id_for_refresh_token(self, refresh_token):
        return None

    async def audit_csrf_failure(self, context, user_id=None, failure_reason="csrf_validation_failed"):
        raise AssertionError("csrf should pass")


class SearchApiService:
    def __init__(self) -> None:
        self.search_called = False
        self.history_called = False

    async def search(self, payload, user, context):
        self.search_called = True
        business = SimpleNamespace(
            id=uuid4(),
            name="ABC Fitness",
            industry=payload.filters.industry,
            website="https://abc.example",
            phone="+123456789",
            email="contact@abc.example",
            country=payload.filters.country,
            state=payload.filters.state,
            city=payload.filters.city,
            address="123 Main Street",
            source_type="directory",
        )
        return SearchResults(
            businesses=[business],
            pagination=PaginationResponse.from_counts(1, 25, 1),
        )

    async def history(self, pagination, user, context):
        self.history_called = True
        item = SimpleNamespace(
            id=uuid4(),
            industry="gym",
            country="United States",
            state="Texas",
            city="Houston",
            results_count=1,
            created_at=datetime.now(timezone.utc),
        )
        return SearchHistoryResults(
            history=[item],
            pagination=PaginationResponse.from_counts(1, 25, 1),
        )

    async def audit_rate_limit_denied(self, user, context, scope="search"):
        raise AssertionError("rate limit should not be denied")


class BusinessApiService:
    def __init__(self) -> None:
        self.contacts_called = False
        self.sources_called = False

    async def get_detail(self, business_id, user, context):
        now = datetime.now(timezone.utc)
        business = SimpleNamespace(
            id=business_id,
            name="ABC Fitness",
            industry="gym",
            website="https://abc.example",
            phone="+123456789",
            email="contact@abc.example",
            country="United States",
            state="Texas",
            city="Houston",
            address="123 Main Street",
            description=None,
            source_type="directory",
            created_at=now,
            updated_at=now,
        )
        return BusinessDetailResult(
            business=business,
            contacts_count=1,
            sources_count=1,
            social_profiles_count=0,
        )

    async def get_contacts(self, business_id, pagination, user, context):
        self.contacts_called = True
        contact = SimpleNamespace(
            id=uuid4(),
            full_name="Public Contact",
            role="Support",
            email="support@abc.example",
            phone="+123456789",
            linkedin_url=None,
            is_decision_maker=False,
            priority_score=0,
            source_url="https://abc.example/contact",
            created_at=datetime.now(timezone.utc),
        )
        return BusinessContactsResult(
            business_id=business_id,
            contacts=[contact],
            pagination=PaginationResponse.from_counts(1, 25, 1),
        )

    async def get_sources(self, business_id, pagination, user, context):
        self.sources_called = True
        data_source = SimpleNamespace(
            id=uuid4(),
            source_type="directory",
            source_url="https://directory.example/abc",
            trust_tier="B",
            confidence_score=80,
            collected_at=datetime.now(timezone.utc),
        )
        return BusinessSourcesResult(
            business_id=business_id,
            data_sources=[data_source],
            pagination=PaginationResponse.from_counts(1, 25, 1),
        )

    async def audit_rate_limit_denied(self, user, context, scope):
        raise AssertionError("rate limit should not be denied")


def auth_cookie_for(user) -> dict[str, str]:
    return {"access_token": create_access_token(str(user.id), user.email, user.role)}


def csrf_headers_and_cookies() -> tuple[dict[str, str], dict[str, str]]:
    csrf_token = generate_csrf_token("anonymous")
    return {"X-CSRF-Token": csrf_token}, {"csrf_token": csrf_token}


def test_search_endpoint_returns_standard_response() -> None:
    user = SimpleNamespace(id=uuid4(), email="user@example.com", role="user", is_active=True)
    service = SearchApiService()
    app.dependency_overrides[get_auth_service] = lambda: SearchAuthService(user)
    app.dependency_overrides[get_search_service] = lambda: service
    client = TestClient(app)
    headers, cookies = csrf_headers_and_cookies()
    cookies.update(auth_cookie_for(user))

    response = client.post(
        "/api/v1/search",
        json={
            "filters": {
                "industry": "gym",
                "country": "United States",
                "state": "Texas",
                "city": "Houston",
            }
        },
        headers=headers,
        cookies=cookies,
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["results"][0]["name"] == "ABC Fitness"
    assert response.json()["data"]["pagination"]["total"] == 1
    assert service.search_called is True


def test_search_history_endpoint_returns_history() -> None:
    user = SimpleNamespace(id=uuid4(), email="user@example.com", role="user", is_active=True)
    service = SearchApiService()
    app.dependency_overrides[get_auth_service] = lambda: SearchAuthService(user)
    app.dependency_overrides[get_search_service] = lambda: service
    client = TestClient(app)

    response = client.get("/api/v1/search/history", cookies=auth_cookie_for(user))

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["history"][0]["industry"] == "gym"
    assert service.history_called is True


def test_business_detail_endpoint_returns_business() -> None:
    user = SimpleNamespace(id=uuid4(), email="user@example.com", role="user", is_active=True)
    business_id = uuid4()
    app.dependency_overrides[get_auth_service] = lambda: SearchAuthService(user)
    app.dependency_overrides[get_business_service] = lambda: BusinessApiService()
    client = TestClient(app)

    response = client.get(f"/api/v1/businesses/{business_id}", cookies=auth_cookie_for(user))

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["business"]["id"] == str(business_id)
    assert response.json()["data"]["business"]["contacts_count"] == 1
    assert "contacts" not in response.json()["data"]


def test_business_contacts_endpoint_returns_paginated_contacts() -> None:
    user = SimpleNamespace(id=uuid4(), email="user@example.com", role="user", is_active=True)
    business_id = uuid4()
    service = BusinessApiService()
    app.dependency_overrides[get_auth_service] = lambda: SearchAuthService(user)
    app.dependency_overrides[get_business_service] = lambda: service
    client = TestClient(app)

    response = client.get(f"/api/v1/businesses/{business_id}/contacts", cookies=auth_cookie_for(user))

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["business_id"] == str(business_id)
    assert response.json()["data"]["contacts"][0]["full_name"] == "Public Contact"
    assert response.json()["data"]["pagination"]["total"] == 1
    assert service.contacts_called is True


def test_business_sources_endpoint_returns_paginated_sources() -> None:
    user = SimpleNamespace(id=uuid4(), email="user@example.com", role="user", is_active=True)
    business_id = uuid4()
    service = BusinessApiService()
    app.dependency_overrides[get_auth_service] = lambda: SearchAuthService(user)
    app.dependency_overrides[get_business_service] = lambda: service
    client = TestClient(app)

    response = client.get(f"/api/v1/businesses/{business_id}/sources", cookies=auth_cookie_for(user))

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["business_id"] == str(business_id)
    assert response.json()["data"]["sources"][0]["source_type"] == "directory"
    assert response.json()["data"]["pagination"]["total"] == 1
    assert service.sources_called is True
