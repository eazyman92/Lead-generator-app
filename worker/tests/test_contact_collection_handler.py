import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from collectors.contact_collection import ContactCollectionService
from collectors.models import RawBusiness, RawContact, RawSocialProfile
from jobs.models import JobSnapshot


def build_job() -> JobSnapshot:
    now = datetime.now(timezone.utc).isoformat()
    return JobSnapshot(
        id=str(uuid4()),
        job_type="contact_collection",
        status="running",
        attempts=1,
        max_attempts=3,
        retry_after=None,
        dead_letter=False,
        dead_letter_reason=None,
        cancelled=False,
        cancelled_reason=None,
        last_error_code=None,
        last_error_at=None,
        locked_at=now,
        locked_by="worker-1",
        error_message=None,
        created_at=now,
        updated_at=now,
    )


class FakeSessionContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def commit(self):
        return None


class FakeRepository:
    def __init__(self, payload):
        self.payload = payload
        self.progress_updates = []
        self.audit_events = []
        self.businesses = []
        self.contacts = []
        self.social_profiles = []
        self.session_factory = lambda: FakeSessionContext()

    async def load_job_payload(self, session, job_id):
        return self.payload

    async def update_progress(self, session, job_id, progress):
        self.progress_updates.append(progress)

    async def audit(self, session, event_type, request_id, user_id, metadata):
        self.audit_events.append(event_type)

    async def save_business(self, session, business):
        self.businesses.append(business)
        return uuid4(), True

    async def save_data_source(self, session, business_id, business):
        return uuid4()

    async def save_contact(self, session, business_id, source_id, contact):
        self.contacts.append(contact)
        return uuid4(), True

    async def save_social_profile(self, session, business_id, profile):
        self.social_profiles.append(profile)
        return uuid4(), True


class FakeProvider:
    async def search(self, payload):
        return [
            RawBusiness(
                name="Example Gym",
                industry="Fitness",
                website="",
                phone="5551234567",
                email=None,
                country="United States",
                state="Texas",
                city="Houston",
                address="123 Main",
                description=None,
                source_type="manual",
                source_url="https://example.com",
                trust_tier="C",
                confidence_score=65,
                contacts=[
                    RawContact(
                        full_name="Public Contact",
                        role="Sales",
                        email="sales@example.com",
                        source_url="https://example.com",
                    )
                ],
                social_profiles=[
                    RawSocialProfile(
                        platform="linkedin",
                        url="https://linkedin.com/company/example",
                    )
                ],
            )
        ]


def test_contact_collection_service_persists_business_contact_source_and_progress() -> None:
    payload = {
        "request_id": "request-1",
        "created_by_user_id": str(uuid4()),
        "idempotency_key": "contact_collection:test",
        "data": {
            "query": "gym",
            "location": "Houston",
            "category": "fitness",
            "limit": 10,
        },
    }
    repository = FakeRepository(payload)
    service = ContactCollectionService(
        SimpleNamespace(
            contact_collection_max_limit=50,
            worker_user_agent="test",
            worker_http_timeout_seconds=1,
        ),
        repository,
        FakeProvider(),
    )

    progress = asyncio.run(service.run(build_job()))

    assert progress.businesses_processed == 1
    assert progress.contacts_saved == 1
    assert repository.businesses[0].name == "Example Gym"
    assert repository.contacts[0].email == "sales@example.com"
    assert {profile.platform for profile in repository.social_profiles} == {"linkedin"}
    assert "contact_collection_completed" in repository.audit_events
    assert repository.progress_updates[-1]["completion_percent"] == 100


def test_contact_collection_service_records_website_social_profile() -> None:
    payload = {
        "request_id": "request-1",
        "created_by_user_id": str(uuid4()),
        "data": {
            "query": "gym",
            "location": "Houston",
            "category": "fitness",
            "limit": 10,
        },
    }
    repository = FakeRepository(payload)

    class WebsiteProvider:
        async def search(self, payload):
            return [
                RawBusiness(
                    name="Website Gym",
                    industry="Fitness",
                    website="https://website-gym.example",
                    phone="5551234567",
                    email=None,
                    country="United States",
                    state="Texas",
                    city="Houston",
                    address="123 Main",
                    description=None,
                    source_type="manual",
                    source_url="",
                    trust_tier="C",
                    confidence_score=65,
                )
            ]

    service = ContactCollectionService(
        SimpleNamespace(
            contact_collection_max_limit=50,
            worker_user_agent="test",
            worker_http_timeout_seconds=1,
        ),
        repository,
        WebsiteProvider(),
    )

    asyncio.run(service.run(build_job()))

    assert repository.social_profiles[0].platform == "website"
