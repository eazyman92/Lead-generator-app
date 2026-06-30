import asyncio
import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs

from collectors.extraction import contacts_from_public_html, social_profiles_from_public_html
from collectors.models import RawBusiness
from collectors.normalization import deterministic_business_identity, normalize_business
from collectors.providers import (
    CompositeBusinessProvider,
    DataForSEOGoogleMapsProvider,
    OpenStreetMapBusinessProvider,
    PayloadBusinessProvider,
    ProviderError,
)


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


def test_contact_extraction_marks_public_decision_makers() -> None:
    html = """
    <html>
      <body>
        <p>Jane Smith - CEO</p>
        <p>Email info@example.com or call +1 (555) 123-4567.</p>
      </body>
    </html>
    """

    contacts = contacts_from_public_html(html, "https://example.com/about")

    decision_makers = [contact for contact in contacts if contact.is_decision_maker]
    assert decision_makers[0].full_name == "Jane Smith"
    assert decision_makers[0].role == "CEO"
    assert decision_makers[0].priority_score == 95


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


def test_dataforseo_provider_parses_google_maps_response() -> None:
    provider = DataForSEOGoogleMapsProvider(
        "login",
        "password",
        timeout_seconds=1,
        default_depth=100,
    )
    response_payload = {
        "tasks": [
            {
                "status_code": 20000,
                "result": [
                    {
                        "items": [
                            {
                                "type": "maps_search",
                                "title": "Example Restaurant",
                                "category": "Restaurant",
                                "phone": "+1 555 123 4567",
                                "url": "https://example-restaurant.test",
                                "domain": "example-restaurant.test",
                                "address": "123 Main Street, Houston, TX",
                                "place_id": "place-123",
                                "cid": "cid-123",
                                "rating": 4.6,
                                "rating_count": 128,
                                "address_info": {
                                    "city": "Houston",
                                    "region": "Texas",
                                    "country_code": "US",
                                },
                            }
                        ]
                    }
                ],
            }
        ]
    }
    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["url"] = request.full_url
        captured_request["data"] = json.loads(request.data.decode("utf-8"))
        captured_request["authorization"] = request.headers["Authorization"]
        captured_request["timeout"] = timeout
        return FakeHttpResponse(response_payload)

    with patch("collectors.providers.urlopen", side_effect=fake_urlopen):
        businesses = asyncio.run(
            provider.search(
                {
                    "request_id": "request-1",
                    "query": "Restaurants",
                    "category": "Restaurants",
                    "country": "United States",
                    "state": "Texas",
                    "city": "Houston",
                    "location": "Houston, Texas, United States",
                    "limit": 100,
                }
            )
        )

    assert captured_request["url"] == DataForSEOGoogleMapsProvider.endpoint
    assert captured_request["data"][0]["keyword"] == "Restaurants"
    assert captured_request["data"][0]["location_name"] == "Houston, Texas, United States"
    assert captured_request["data"][0]["depth"] == 100
    assert captured_request["authorization"].startswith("Basic ")
    assert captured_request["timeout"] == 1
    assert businesses[0].name == "Example Restaurant"
    assert businesses[0].website == "https://example-restaurant.test"
    assert businesses[0].phone == "+1 555 123 4567"
    assert businesses[0].source_type == "dataforseo_google_maps"
    assert businesses[0].contacts[0].phone == "+1 555 123 4567"


def test_dataforseo_provider_reports_account_not_ready_from_http_error() -> None:
    provider = DataForSEOGoogleMapsProvider(
        "login",
        "password",
        timeout_seconds=1,
        default_depth=100,
    )
    error = HTTPError(
        DataForSEOGoogleMapsProvider.endpoint,
        402,
        "Payment Required",
        {},
        BytesIO(b'{"status_message":"Please add funds to your balance."}'),
    )

    with patch("collectors.providers.urlopen", side_effect=error):
        try:
            asyncio.run(
                provider.search(
                    {
                        "request_id": "request-1",
                        "query": "Restaurants",
                        "category": "Restaurants",
                        "country": "United States",
                        "state": "Texas",
                        "city": "Houston",
                        "location": "Houston, Texas, United States",
                        "limit": 100,
                    }
                )
            )
        except ProviderError as exc:
            assert exc.code == "PROVIDER_ACCOUNT_NOT_READY"
            assert exc.retryable is False
        else:
            raise AssertionError("account setup errors should raise ProviderError")


def test_composite_provider_falls_back_after_dataforseo_account_failure() -> None:
    class AccountBlockedProvider:
        name = "dataforseo_google_maps"

        async def search(self, payload):
            raise ProviderError(
                "PROVIDER_ACCOUNT_NOT_READY",
                "Provider account requires verification or funds before fetching data.",
                False,
                self.name,
            )

    class OverpassFallbackProvider:
        name = "openstreetmap"

        async def search(self, payload):
            return [
                RawBusiness(
                    name="Fallback Restaurant",
                    industry="Restaurants",
                    website="",
                    phone="+1 555 123 4567",
                    email=None,
                    country="United States",
                    state="Texas",
                    city="Houston",
                    address="123 Main",
                    description=None,
                    source_type="directory",
                    source_url="https://www.openstreetmap.org/node/123",
                    trust_tier="C",
                    confidence_score=65,
                )
            ]

    provider = CompositeBusinessProvider([AccountBlockedProvider(), OverpassFallbackProvider()])

    businesses = asyncio.run(
        provider.search(
            {
                "request_id": "request-1",
                "query": "Restaurants",
                "category": "Restaurants",
                "country": "United States",
                "state": "Texas",
                "city": "Houston",
                "location": "Houston, Texas, United States",
                "limit": 20,
            }
        )
    )

    assert businesses[0].name == "Fallback Restaurant"
    assert businesses[0].source_type == "directory"


def test_openstreetmap_provider_parses_houston_restaurants_from_overpass() -> None:
    provider = OpenStreetMapBusinessProvider("test-agent", timeout_seconds=1)
    response_payload = {
        "elements": [
            {
                "type": "node",
                "id": 123,
                "lat": 29.7604,
                "lon": -95.3698,
                "tags": {
                    "amenity": "restaurant",
                    "name": "Example Restaurant",
                    "website": "https://example-restaurant.test",
                    "phone": "+1 555 123 4567",
                    "addr:housenumber": "123",
                    "addr:street": "Main Street",
                    "addr:city": "Houston",
                    "addr:state": "Texas",
                    "addr:country": "United States",
                },
            },
            {
                "type": "way",
                "id": 456,
                "center": {"lat": 29.761, "lon": -95.37},
                "tags": {
                    "amenity": "restaurant",
                    "name": "Way Restaurant",
                },
            },
            {
                "type": "relation",
                "id": 789,
                "center": {"lat": 29.762, "lon": -95.371},
                "tags": {
                    "amenity": "restaurant",
                    "name": "Relation Restaurant",
                },
            },
        ]
    }
    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["url"] = request.full_url
        captured_request["data"] = request.data.decode("utf-8")
        captured_request["timeout"] = timeout
        return FakeHttpResponse(response_payload)

    with patch("collectors.providers.urlopen", side_effect=fake_urlopen):
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

    overpass_query = parse_qs(captured_request["data"])["data"][0]
    assert captured_request["url"] == "https://overpass-api.de/api/interpreter"
    assert captured_request["timeout"] == 1
    assert '["amenity"="restaurant"]' in overpass_query
    assert "(29.52,-95.82,30.12,-95.0)" in overpass_query
    assert "area.searchArea" not in overpass_query
    assert "Restaurants Restaurants" not in overpass_query
    assert "nominatim.openstreetmap.org" not in captured_request["url"]
    assert len(businesses) == 3
    assert businesses[0].name == "Example Restaurant"
    assert businesses[0].source_type == "directory"
    assert businesses[0].source_url == "https://www.openstreetmap.org/node/123"
    assert businesses[0].country == "United States"
    assert businesses[0].state == "Texas"
    assert businesses[0].city == "Houston"


def test_openstreetmap_provider_tries_next_endpoint_after_retryable_failure() -> None:
    provider = OpenStreetMapBusinessProvider(
        "test-agent",
        timeout_seconds=1,
        endpoints=[
            "https://overpass-primary.test/api/interpreter",
            "https://overpass-secondary.test/api/interpreter",
        ],
    )
    response_payload = {
        "elements": [
            {
                "type": "node",
                "id": 123,
                "lat": 29.7604,
                "lon": -95.3698,
                "tags": {
                    "amenity": "restaurant",
                    "name": "Fallback Endpoint Restaurant",
                    "addr:city": "Houston",
                    "addr:state": "Texas",
                    "addr:country": "United States",
                },
            }
        ]
    }
    attempted_urls = []

    def fake_urlopen(request, timeout):
        attempted_urls.append(request.full_url)
        if len(attempted_urls) == 1:
            raise HTTPError(
                request.full_url,
                504,
                "Gateway Timeout",
                {},
                BytesIO(b"Overpass timeout"),
            )
        return FakeHttpResponse(response_payload)

    with patch("collectors.providers.urlopen", side_effect=fake_urlopen):
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

    assert attempted_urls == [
        "https://overpass-primary.test/api/interpreter",
        "https://overpass-secondary.test/api/interpreter",
    ]
    assert businesses[0].name == "Fallback Endpoint Restaurant"


def test_openstreetmap_provider_parses_ikeja_restaurants_from_overpass_fixture() -> None:
    provider = OpenStreetMapBusinessProvider("test-agent", timeout_seconds=1)
    response_payload = {
        "elements": [
            {
                "type": "node",
                "id": 1001,
                "tags": {
                    "amenity": "restaurant",
                    "name": "Ikeja Kitchen",
                    "contact:phone": "+234 800 123 4567",
                    "addr:city": "Ikeja",
                    "addr:state": "Lagos",
                    "addr:country": "Nigeria",
                },
            }
        ]
    }
    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["data"] = request.data.decode("utf-8")
        return FakeHttpResponse(response_payload)

    with patch("collectors.providers.urlopen", side_effect=fake_urlopen):
        businesses = asyncio.run(
            provider.search(
                {
                    "request_id": "request-2",
                    "query": "Restaurants",
                    "category": "Restaurants",
                    "location": "Ikeja, Lagos, Nigeria",
                    "country": "Nigeria",
                    "state": "Lagos",
                    "city": "Ikeja",
                    "limit": 20,
                }
            )
        )

    overpass_query = parse_qs(captured_request["data"])["data"][0]
    assert '["amenity"="restaurant"]' in overpass_query
    assert "(6.55,3.28,6.66,3.43)" in overpass_query
    assert "area.searchArea" not in overpass_query
    assert businesses[0].name == "Ikeja Kitchen"
    assert businesses[0].source_url == "https://www.openstreetmap.org/node/1001"
    assert businesses[0].phone == "+234 800 123 4567"
    assert businesses[0].country == "Nigeria"
    assert businesses[0].state == "Lagos"
    assert businesses[0].city == "Ikeja"


def test_openstreetmap_provider_reports_empty_response() -> None:
    provider = OpenStreetMapBusinessProvider("test-agent", timeout_seconds=1)

    with patch("collectors.providers.urlopen", return_value=FakeHttpResponse({"elements": []})):
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

    with patch(
        "collectors.providers.urlopen",
        return_value=FakeHttpResponse({"elements": [{"type": "node", "id": 123}]}),
    ):
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
