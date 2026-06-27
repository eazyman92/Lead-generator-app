import asyncio
import json
from unittest.mock import patch

from collectors.extraction import contacts_from_public_html, social_profiles_from_public_html
from collectors.models import RawBusiness
from collectors.normalization import deterministic_business_identity, normalize_business
from collectors.providers import OpenStreetMapBusinessProvider, PayloadBusinessProvider, ProviderError


class FakeHttpResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_business_normalization_and_identity_are_deterministic() -> None:
    business = normalize_business(
        RawBusiness(
            name="  ACME GYM  ",
            industry="fitness",
            website="HTTPS://Example.COM/",
            phone="(555) 123-4567",
            email=" INFO@EXAMPLE.COM ",
            country="united states",
            state="texas",
            city="houston",
            address="  123 Main St  ",
            description=None,
            source_type="directory",
            source_url="example.com/contact",
            trust_tier="C",
            confidence_score=65,
        )
    )

    assert business.name == "Acme Gym"
    assert business.website == "https://example.com"
    assert business.phone == "5551234567"
    assert business.email == "info@example.com"
    assert deterministic_business_identity(business) == "website:https://example.com"


def test_contact_and_social_extraction_from_public_html() -> None:
    html = """
    <html>
      <body>
        Email sales@example.com or call +1 (555) 123-4567.
        <a href="https://www.linkedin.com/company/example">LinkedIn</a>
        <a href="https://www.facebook.com/example">Facebook</a>
        <a href="https://x.com/example">X</a>
        <a href="https://www.youtube.com/@example">YouTube</a>
      </body>
    </html>
    """

    contacts = contacts_from_public_html(html, "https://example.com/contact")
    profiles = social_profiles_from_public_html(html, "https://example.com/contact")

    assert contacts[0].email == "sales@example.com"
    assert contacts[0].role == "Sales"
    assert {profile.platform for profile in profiles} == {
        "linkedin",
        "facebook",
        "x",
        "youtube",
    }


def test_payload_provider_returns_payload_businesses() -> None:
    provider = PayloadBusinessProvider()

    businesses = asyncio.run(
        provider.search(
            {
                "businesses": [
                    {
                        "name": "Example Gym",
                        "industry": "Fitness",
                        "website": "https://example.com",
                        "phone": "5551234567",
                        "country": "United States",
                        "state": "Texas",
                        "city": "Houston",
                        "address": "123 Main",
                        "contacts": [{"email": "contact@example.com"}],
                    }
                ]
            }
        )
    )

    assert businesses[0].name == "Example Gym"
    assert businesses[0].contacts[0].email == "contact@example.com"


def test_payload_provider_does_not_convert_search_query_to_manual_business() -> None:
    provider = PayloadBusinessProvider()

    businesses = asyncio.run(
        provider.search(
            {
                "query": "Restaurants",
                "category": "Restaurants",
                "location": "Ikeja, Lagos, Nigeria",
                "country": "Nigeria",
                "state": "Lagos",
                "city": "Ikeja",
            }
        )
    )

    assert businesses == []


def test_openstreetmap_provider_parses_successful_response() -> None:
    provider = OpenStreetMapBusinessProvider("test-agent", timeout_seconds=1)
    response_payload = [
        {
            "osm_type": "node",
            "osm_id": 123,
            "name": "Example Restaurant",
            "display_name": "Example Restaurant, Houston, Texas, United States",
            "type": "restaurant",
            "address": {
                "city": "Houston",
                "state": "Texas",
                "country": "United States",
            },
            "extratags": {
                "website": "https://example-restaurant.test",
                "phone": "+1 555 123 4567",
            },
        }
    ]

    with patch("collectors.providers.urlopen", return_value=FakeHttpResponse(response_payload)):
        businesses = asyncio.run(
            provider.search(
                {
                    "request_id": "request-1",
                    "query": "Restaurants",
                    "category": "Restaurants",
                    "location": "Houston, Texas, United States",
                    "country": "United States",
                    "state": "Texas",
                    "city": "Houston",
                    "limit": 20,
                }
            )
        )

    assert businesses[0].name == "Example Restaurant"
    assert businesses[0].source_type == "directory"
    assert businesses[0].source_url == "https://www.openstreetmap.org/node/123"
    assert businesses[0].country == "United States"
    assert businesses[0].state == "Texas"
    assert businesses[0].city == "Houston"


def test_openstreetmap_provider_reports_empty_response() -> None:
    provider = OpenStreetMapBusinessProvider("test-agent", timeout_seconds=1)

    with patch("collectors.providers.urlopen", return_value=FakeHttpResponse([])):
        try:
            asyncio.run(
                provider.search(
                    {
                        "request_id": "request-1",
                        "query": "Restaurants",
                        "category": "Restaurants",
                        "location": "London, England, United Kingdom",
                        "limit": 20,
                    }
                )
            )
        except ProviderError as exc:
            assert exc.code == "EMPTY_PROVIDER_RESPONSE"
        else:
            raise AssertionError("empty response should raise ProviderError")


def test_openstreetmap_provider_reports_filtered_all_results() -> None:
    provider = OpenStreetMapBusinessProvider("test-agent", timeout_seconds=1)

    with patch("collectors.providers.urlopen", return_value=FakeHttpResponse([{"osm_id": 123}])):
        try:
            asyncio.run(
                provider.search(
                    {
                        "request_id": "request-1",
                        "query": "Restaurants",
                        "category": "Restaurants",
                        "location": "Ikeja, Lagos, Nigeria",
                        "limit": 20,
                    }
                )
            )
        except ProviderError as exc:
            assert exc.code == "FILTERED_ALL_RESULTS"
        else:
            raise AssertionError("rejected candidates should raise ProviderError")
