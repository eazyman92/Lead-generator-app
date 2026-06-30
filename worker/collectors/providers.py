import asyncio
import base64
import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from collectors.models import RawBusiness, RawContact, RawSocialProfile
from collectors.normalization import normalize_url
from config.logging import get_logger

logger = get_logger(__name__)
RAW_RESPONSE_LOG_LIMIT = 2000


def truncate_for_log(value: str, limit: int = RAW_RESPONSE_LOG_LIMIT) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...<truncated>"


@dataclass(frozen=True)
class ProviderError(Exception):
    code: str
    message: str
    retryable: bool
    provider: str

    def __str__(self) -> str:
        return self.message


class BusinessSearchProvider(Protocol):
    name: str

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        """Return raw businesses from a provider-specific source."""


class PayloadBusinessProvider:
    """Provider for deterministic jobs where businesses are supplied in the job payload."""

    name = "payload"

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        businesses = payload.get("businesses") or []
        if not businesses:
            logger.info(
                "provider_skipped",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": self.name,
                    "reason": "no_payload_businesses",
                },
            )
            return []
        return [self._from_payload(item, payload) for item in businesses]

    def _from_payload(self, item: dict[str, Any], root_payload: dict[str, Any]) -> RawBusiness:
        contacts = [
            RawContact(
                full_name=contact.get("full_name", "Public Contact"),
                role=contact.get("role"),
                email=contact.get("email"),
                phone=contact.get("phone"),
                linkedin_url=contact.get("linkedin_url"),
                source_url=(
                    contact.get("source_url") or item.get("source_url") or item.get("website", "")
                ),
            )
            for contact in item.get("contacts", [])
        ]
        profiles = [
            RawSocialProfile(platform=profile["platform"], url=profile["url"])
            for profile in item.get("social_profiles", [])
            if profile.get("platform") and profile.get("url")
        ]
        source_url = (
            item.get("source_url") or item.get("website") or root_payload.get("source_url", "")
        )
        return RawBusiness(
            name=(
                item.get("name")
                or item.get("query")
                or root_payload.get("query", "Unknown Business")
            ),
            industry=item.get("industry") or root_payload.get("category", "Unknown"),
            website=item.get("website", ""),
            phone=item.get("phone", ""),
            email=item.get("email"),
            country=item.get("country") or root_payload.get("country", ""),
            state=item.get("state") or root_payload.get("state", ""),
            city=item.get("city") or root_payload.get("location", ""),
            address=item.get("address") or root_payload.get("location", ""),
            description=item.get("description"),
            source_type=item.get("source_type", "manual"),
            source_url=source_url,
            trust_tier=item.get("trust_tier", "C"),
            confidence_score=int(item.get("confidence_score", 65)),
            contacts=contacts,
            social_profiles=profiles,
        )


class DataForSEOGoogleMapsProvider:
    """Commercial Google Maps discovery provider backed by DataForSEO."""

    name = "dataforseo_google_maps"
    endpoint = "https://api.dataforseo.com/v3/serp/google/maps/live/advanced"

    def __init__(
        self,
        login: str,
        password: str,
        timeout_seconds: int = 30,
        default_depth: int = 100,
    ) -> None:
        self.login = login
        self.password = password
        self.timeout_seconds = timeout_seconds
        self.default_depth = max(1, min(int(default_depth), 700))

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        request_payload = self._request_payload(payload)
        logger.info(
            "provider_request",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "endpoint": self.endpoint,
                "keyword": request_payload[0]["keyword"],
                "location_name": request_payload[0]["location_name"],
                "depth": request_payload[0]["depth"],
                "http_timeout_seconds": self.timeout_seconds,
            },
        )
        return await asyncio.to_thread(self._search_sync, request_payload, payload)

    def _request_payload(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        keyword = str(payload.get("category") or payload.get("query") or "").strip()
        location_name = (
            ", ".join(
                part
                for part in (
                    payload.get("city"),
                    payload.get("state"),
                    payload.get("country"),
                )
                if part
            )
            or str(payload.get("location") or "").strip()
        )
        depth = max(1, min(int(payload.get("limit") or self.default_depth), 700))
        if not keyword or not location_name:
            raise ProviderError(
                "INVALID_PROVIDER_QUERY",
                "DataForSEO Google Maps provider requires a keyword and location.",
                False,
                self.name,
            )
        return [
            {
                "keyword": keyword,
                "location_name": location_name,
                "language_code": "en",
                "depth": depth,
            }
        ]

    def _search_sync(
        self,
        request_payload: list[dict[str, Any]],
        root_payload: dict[str, Any],
    ) -> list[RawBusiness]:
        request = Request(
            self.endpoint,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "Authorization": f"Basic {self._auth_token()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = self._read_http_error_body(exc)
            code, message, retryable = self._classify_http_error(exc.code, error_body)
            logger.warning(
                "provider_response_failed",
                extra={
                    "request_id": root_payload.get("request_id", "unknown"),
                    "provider": self.name,
                    "status": exc.code,
                    "error_code": code,
                    "endpoint": self.endpoint,
                    "raw_body": truncate_for_log(error_body),
                    "raw_body_length": len(error_body),
                },
            )
            raise ProviderError(
                code,
                message,
                retryable,
                self.name,
            ) from exc
        except TimeoutError as exc:
            raise ProviderError(
                "NETWORK_TIMEOUT",
                "Provider request timed out.",
                True,
                self.name,
            ) from exc
        except URLError as exc:
            raise ProviderError(
                "DNS_FAILURE",
                "Provider could not be resolved.",
                True,
                self.name,
            ) from exc

        logger.info(
            "provider_raw_response",
            extra={
                "request_id": root_payload.get("request_id", "unknown"),
                "provider": self.name,
                "status": status,
                "endpoint": self.endpoint,
                "raw_body": truncate_for_log(body),
                "raw_body_length": len(body),
            },
        )
        try:
            response_payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "INVALID_PROVIDER_RESPONSE",
                "Provider returned invalid JSON.",
                False,
                self.name,
            ) from exc

        items = self._extract_items(response_payload)
        parsed = self._parse_items(items, root_payload)
        logger.info(
            "provider_response",
            extra={
                "request_id": root_payload.get("request_id", "unknown"),
                "provider": self.name,
                "status": status,
                "endpoint": self.endpoint,
                "raw_response_size": len(body),
                "parsed_objects": len(items),
                "businesses_returned": len(parsed),
            },
        )
        if not items:
            raise ProviderError(
                "EMPTY_PROVIDER_RESPONSE",
                "Provider returned an empty result set.",
                False,
                self.name,
            )
        if not parsed:
            raise ProviderError(
                "FILTERED_ALL_RESULTS",
                "Provider results were parsed but no candidate was accepted.",
                False,
                self.name,
            )
        return parsed

    def _auth_token(self) -> str:
        return base64.b64encode(f"{self.login}:{self.password}".encode("utf-8")).decode("ascii")

    def _extract_items(self, response_payload: Any) -> list[dict[str, Any]]:
        if not isinstance(response_payload, dict):
            raise ProviderError(
                "INVALID_PROVIDER_RESPONSE",
                "Provider returned an invalid response shape.",
                False,
                self.name,
            )
        items: list[dict[str, Any]] = []
        for task in response_payload.get("tasks") or []:
            if not isinstance(task, dict):
                continue
            if int(task.get("status_code") or 20000) >= 40000:
                code, message, retryable = self._classify_task_error(task)
                raise ProviderError(
                    code,
                    message,
                    retryable,
                    self.name,
                )
            for result in task.get("result") or []:
                if not isinstance(result, dict):
                    continue
                items.extend(item for item in result.get("items") or [] if isinstance(item, dict))
        return items

    def _parse_items(
        self,
        items: list[dict[str, Any]],
        payload: dict[str, Any],
    ) -> list[RawBusiness]:
        businesses: list[RawBusiness] = []
        for item in items:
            title = item.get("title") or item.get("name")
            if not title:
                continue
            business = self._from_dataforseo_item(item, payload)
            businesses.append(business)
            logger.info(
                "provider_candidate_decision",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": self.name,
                    "accepted": True,
                    "reason": "accepted",
                    "business_name": business.name,
                    "place_id": item.get("place_id"),
                    "cid": item.get("cid"),
                    "source_url": business.source_url,
                },
            )
        return businesses

    def _read_http_error_body(self, exc: HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _classify_http_error(self, status: int, body: str) -> tuple[str, str, bool]:
        body_text = body.lower()
        if status in {401, 403}:
            return (
                "PROVIDER_AUTH_FAILED",
                "Provider credentials were rejected.",
                False,
            )
        if status == 402 or self._looks_like_billing_or_verification_error(body_text):
            return (
                "PROVIDER_ACCOUNT_NOT_READY",
                "Provider account requires verification or funds before fetching data.",
                False,
            )
        if status == 429:
            return ("HTTP_429", "Provider rate limit was reached.", True)
        if status >= 500:
            return ("HTTP_5XX", "Provider service returned a server error.", True)
        return ("PROVIDER_FAILURE", "Provider request failed.", False)

    def _classify_task_error(self, task: dict[str, Any]) -> tuple[str, str, bool]:
        status_code = int(task.get("status_code") or 0)
        status_message = str(task.get("status_message") or "Provider task failed.")
        message_text = status_message.lower()
        if "auth" in message_text or "login" in message_text or "password" in message_text:
            return ("PROVIDER_AUTH_FAILED", "Provider credentials were rejected.", False)
        if self._looks_like_billing_or_verification_error(message_text):
            return (
                "PROVIDER_ACCOUNT_NOT_READY",
                "Provider account requires verification or funds before fetching data.",
                False,
            )
        if status_code in {40200, 40201, 40202}:
            return (
                "PROVIDER_ACCOUNT_NOT_READY",
                "Provider account requires verification or funds before fetching data.",
                False,
            )
        return ("PROVIDER_FAILURE", status_message, True)

    def _looks_like_billing_or_verification_error(self, text: str) -> bool:
        indicators = (
            "balance",
            "billing",
            "fund",
            "payment",
            "verify",
            "verification",
            "account setup",
            "not enough money",
            "insufficient",
        )
        return any(indicator in text for indicator in indicators)

    def _from_dataforseo_item(self, item: dict[str, Any], payload: dict[str, Any]) -> RawBusiness:
        address_info = (
            item.get("address_info") if isinstance(item.get("address_info"), dict) else {}
        )
        website = normalize_url(item.get("url") or item.get("domain") or item.get("contact_url"))
        phone = item.get("phone") or ""
        source_url = item.get("check_url") or item.get("url") or ""
        if not source_url and item.get("place_id"):
            source_url = f"https://www.google.com/maps/place/?q=place_id:{item.get('place_id')}"
        category = (
            item.get("category") or payload.get("category") or payload.get("query") or "Unknown"
        )
        description_parts = [
            part
            for part in (
                f"rating={item.get('rating')}" if item.get("rating") is not None else None,
                f"reviews={item.get('rating_count')}"
                if item.get("rating_count") is not None
                else None,
                f"cid={item.get('cid')}" if item.get("cid") else None,
                f"place_id={item.get('place_id')}" if item.get("place_id") else None,
            )
            if part
        ]
        return RawBusiness(
            name=str(item.get("title") or item.get("name")),
            industry=str(category),
            website=website,
            phone=str(phone or ""),
            email=None,
            country=payload.get("country") or address_info.get("country_code") or "",
            state=payload.get("state") or address_info.get("region") or "",
            city=payload.get("city") or address_info.get("city") or "",
            address=item.get("address")
            or address_info.get("address")
            or payload.get("location", ""),
            description="; ".join(description_parts) or None,
            source_type="dataforseo_google_maps",
            source_url=source_url or website or "https://www.google.com/maps",
            trust_tier="B",
            confidence_score=80,
            contacts=[
                RawContact(
                    full_name="Public Contact",
                    role="General Contact",
                    phone=str(phone),
                    source_url=source_url or website or "https://www.google.com/maps",
                )
            ]
            if phone
            else [],
            social_profiles=[],
        )


class OpenStreetMapBusinessProvider:
    """Public business discovery provider backed by OpenStreetMap Overpass."""

    name = "openstreetmap"
    endpoint = "https://overpass-api.de/api/interpreter"
    default_endpoints = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter",
    )
    category_tags: dict[str, tuple[tuple[str, str], ...]] = {
        "automotive": (
            ("shop", "car"),
            ("shop", "car_repair"),
            ("shop", "tyres"),
            ("amenity", "car_wash"),
            ("amenity", "fuel"),
        ),
        "beauty and wellness": (
            ("shop", "beauty"),
            ("shop", "hairdresser"),
            ("shop", "massage"),
            ("leisure", "fitness_centre"),
            ("amenity", "spa"),
        ),
        "construction": (
            ("shop", "doityourself"),
            ("shop", "hardware"),
            ("shop", "building_materials"),
            ("office", "architect"),
            ("craft", "builder"),
        ),
        "education": (
            ("amenity", "school"),
            ("amenity", "college"),
            ("amenity", "university"),
            ("amenity", "kindergarten"),
            ("amenity", "language_school"),
        ),
        "financial services": (
            ("amenity", "bank"),
            ("amenity", "atm"),
            ("office", "accountant"),
            ("office", "financial"),
            ("shop", "money_lender"),
        ),
        "healthcare": (
            ("amenity", "hospital"),
            ("amenity", "clinic"),
            ("amenity", "doctors"),
            ("amenity", "dentist"),
            ("amenity", "pharmacy"),
        ),
        "hospitality": (
            ("tourism", "hotel"),
            ("tourism", "guest_house"),
            ("tourism", "hostel"),
            ("tourism", "motel"),
            ("amenity", "restaurant"),
        ),
        "legal services": (
            ("office", "lawyer"),
            ("office", "notary"),
        ),
        "logistics": (
            ("amenity", "post_office"),
            ("office", "logistics"),
            ("shop", "storage_rental"),
            ("industrial", "warehouse"),
            ("amenity", "courier"),
        ),
        "manufacturing": (
            ("landuse", "industrial"),
            ("industrial", "factory"),
            ("man_made", "works"),
        ),
        "marketing agencies": (
            ("office", "advertising_agency"),
            ("office", "marketing"),
            ("office", "company"),
        ),
        "real estate": (
            ("office", "estate_agent"),
        ),
        "retail": (
            ("shop", "supermarket"),
            ("shop", "convenience"),
            ("shop", "department_store"),
            ("shop", "clothes"),
            ("shop", "mall"),
        ),
        "accountants": (("office", "accountant"),),
        "accounting": (("office", "accountant"),),
        "atm": (("amenity", "atm"),),
        "atms": (("amenity", "atm"),),
        "bank": (("amenity", "bank"),),
        "banks": (("amenity", "bank"),),
        "bar": (("amenity", "bar"),),
        "bars": (("amenity", "bar"),),
        "cafe": (("amenity", "cafe"),),
        "cafes": (("amenity", "cafe"),),
        "clinic": (("amenity", "clinic"),),
        "clinics": (("amenity", "clinic"),),
        "dentist": (("amenity", "dentist"),),
        "dentists": (("amenity", "dentist"),),
        "doctors": (("amenity", "doctors"),),
        "gym": (("leisure", "fitness_centre"),),
        "gyms": (("leisure", "fitness_centre"),),
        "hospital": (("amenity", "hospital"),),
        "hospitals": (("amenity", "hospital"),),
        "hotel": (("tourism", "hotel"),),
        "hotels": (("tourism", "hotel"),),
        "law firm": (("office", "lawyer"),),
        "law firms": (("office", "lawyer"),),
        "lawyer": (("office", "lawyer"),),
        "lawyers": (("office", "lawyer"),),
        "pharmacy": (("amenity", "pharmacy"),),
        "pharmacies": (("amenity", "pharmacy"),),
        "restaurant": (("amenity", "restaurant"),),
        "restaurants": (("amenity", "restaurant"),),
        "school": (("amenity", "school"),),
        "schools": (("amenity", "school"),),
        "supermarket": (("shop", "supermarket"),),
        "supermarkets": (("shop", "supermarket"),),
    }
    city_bounding_boxes = {
        ("nigeria", "lagos", "ikeja"): (6.55, 3.28, 6.66, 3.43),
        ("nigeria", "lagos", "lekki"): (6.40, 3.45, 6.52, 3.65),
        ("nigeria", "lagos", "victoria island"): (6.41, 3.39, 6.46, 3.46),
        ("nigeria", "lagos", "surulere"): (6.48, 3.32, 6.53, 3.38),
        ("nigeria", "lagos", "yaba"): (6.50, 3.36, 6.54, 3.41),
        ("nigeria", "abuja federal capital territory", "abuja"): (8.85, 7.25, 9.20, 7.65),
        ("nigeria", "abuja federal capital territory", "gwarinpa"): (9.05, 7.37, 9.13, 7.46),
        ("nigeria", "abuja federal capital territory", "maitama"): (9.07, 7.47, 9.11, 7.52),
        ("nigeria", "rivers", "port harcourt"): (4.74, 6.90, 4.90, 7.08),
        ("nigeria", "rivers", "bonny"): (4.38, 7.10, 4.52, 7.28),
        ("united states", "texas", "houston"): (29.52, -95.82, 30.12, -95.00),
        ("united states", "texas", "austin"): (30.10, -97.94, 30.52, -97.56),
        ("united states", "texas", "dallas"): (32.61, -97.00, 33.02, -96.52),
        ("united kingdom", "england", "london"): (51.28, -0.51, 51.70, 0.33),
    }

    def __init__(
        self,
        user_agent: str,
        timeout_seconds: int = 10,
        endpoints: str | list[str] | tuple[str, ...] | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.endpoints = self._normalize_endpoints(endpoints)

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        tags = self._tags_for_payload(payload)
        query, search_mode = self._build_overpass_query(payload, tags)
        limit = int(payload.get("limit", 10))
        logger.info(
            "provider_request",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "endpoint": self.endpoints[0],
                "overpass_endpoints": self.endpoints,
                "overpass_query": query,
                "overpass_search_mode": search_mode,
                "osm_tags": [{"key": tag_key, "value": tag_value} for tag_key, tag_value in tags],
                "limit": max(1, min(limit, 50)),
                "http_timeout_seconds": self.timeout_seconds,
            },
        )
        return await asyncio.to_thread(self._search_sync, query, payload, search_mode)

    def _search_sync(
        self,
        query: str,
        payload: dict[str, Any],
        search_mode: str,
    ) -> list[RawBusiness]:
        last_retryable_error: ProviderError | None = None
        for endpoint in self.endpoints:
            try:
                return self._search_endpoint(endpoint, query, payload, search_mode)
            except ProviderError as exc:
                logger.warning(
                    "provider_endpoint_failed",
                    extra={
                        "request_id": payload.get("request_id", "unknown"),
                        "provider": self.name,
                        "endpoint": endpoint,
                        "error_code": exc.code,
                        "retryable": exc.retryable,
                        "failure_reason": exc.message,
                        "fallback_available": endpoint != self.endpoints[-1],
                    },
                )
                if not exc.retryable:
                    raise
                last_retryable_error = exc
        if last_retryable_error is not None:
            raise ProviderError(
                last_retryable_error.code,
                "OpenStreetMap Overpass endpoints are temporarily unavailable.",
                True,
                self.name,
            ) from last_retryable_error
        return []

    def _search_endpoint(
        self,
        endpoint: str,
        query: str,
        payload: dict[str, Any],
        search_mode: str,
    ) -> list[RawBusiness]:
        request = Request(
            endpoint,
            data=urlencode({"data": query}).encode("utf-8"),
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = self._read_http_error_body(exc)
            code = (
                "HTTP_429"
                if exc.code == 429
                else "HTTP_5XX"
                if exc.code >= 500
                else "PROVIDER_FAILURE"
            )
            logger.warning(
                "provider_response_failed",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": self.name,
                    "status": exc.code,
                    "error_code": code,
                    "endpoint": endpoint,
                    "overpass_search_mode": search_mode,
                    "raw_body": truncate_for_log(error_body),
                    "raw_body_length": len(error_body),
                },
            )
            raise ProviderError(
                code,
                "Provider request failed.",
                exc.code == 429 or exc.code >= 500,
                self.name,
            ) from exc
        except TimeoutError as exc:
            raise ProviderError(
                "NETWORK_TIMEOUT",
                "Provider request timed out.",
                True,
                self.name,
            ) from exc
        except URLError as exc:
            raise ProviderError(
                "DNS_FAILURE",
                "Provider could not be resolved.",
                True,
                self.name,
            ) from exc

        logger.info(
            "provider_raw_response",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "status": status,
                "endpoint": endpoint,
                "overpass_query": query,
                "overpass_search_mode": search_mode,
                "raw_body": truncate_for_log(body),
                "raw_body_length": len(body),
            },
        )
        try:
            response_payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "INVALID_PROVIDER_RESPONSE",
                "Provider returned invalid JSON.",
                False,
                self.name,
            ) from exc
        if not isinstance(response_payload, dict) or not isinstance(
            response_payload.get("elements"),
            list,
        ):
            raise ProviderError(
                "INVALID_PROVIDER_RESPONSE",
                "Provider returned an invalid response shape.",
                False,
                self.name,
            )
        elements = response_payload["elements"]
        parsed = self._parse_results(elements, payload, query, status)
        logger.info(
            "provider_response",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "status": status,
                "endpoint": endpoint,
                "overpass_search_mode": search_mode,
                "raw_response_size": len(body),
                "parsed_objects": len(elements),
                "businesses_returned": len(parsed),
            },
        )
        if not elements:
            raise ProviderError(
                "EMPTY_PROVIDER_RESPONSE",
                "Provider returned an empty result set.",
                False,
                self.name,
            )
        if not parsed:
            raise ProviderError(
                "FILTERED_ALL_RESULTS",
                "Provider results were parsed but no candidate was accepted.",
                False,
                self.name,
            )
        return parsed

    def _normalize_endpoints(
        self,
        endpoints: str | list[str] | tuple[str, ...] | None,
    ) -> list[str]:
        if endpoints is None:
            return list(self.default_endpoints)
        if isinstance(endpoints, str):
            values = [endpoint.strip() for endpoint in endpoints.split(",")]
        else:
            values = [str(endpoint).strip() for endpoint in endpoints]
        normalized = [endpoint for endpoint in values if endpoint]
        return normalized or list(self.default_endpoints)

    def _read_http_error_body(self, exc: HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _parse_results(
        self,
        results: list[Any],
        payload: dict[str, Any],
        query: str,
        status: int,
    ) -> list[RawBusiness]:
        businesses: list[RawBusiness] = []
        for index, item in enumerate(results):
            if not isinstance(item, dict):
                self._log_candidate_decision(
                    payload,
                    query,
                    status,
                    index,
                    False,
                    "candidate_not_object",
                    {"candidate_type": type(item).__name__},
                )
                continue

            tags = item.get("tags") if isinstance(item.get("tags"), dict) else {}
            name = tags.get("name") or tags.get("brand") or tags.get("operator")
            osm_id = item.get("id")
            osm_type = item.get("type")
            if not name:
                self._log_candidate_decision(
                    payload,
                    query,
                    status,
                    index,
                    False,
                    "missing_business_name",
                    {"osm_id": osm_id},
                )
                continue

            business = self._from_osm(item, payload)
            businesses.append(business)
            self._log_candidate_decision(
                payload,
                query,
                status,
                index,
                True,
                "accepted",
                {
                    "osm_id": osm_id,
                    "osm_type": osm_type,
                    "business_name": business.name,
                    "source_url": business.source_url,
                },
            )
        return businesses

    def _log_candidate_decision(
        self,
        payload: dict[str, Any],
        query: str,
        status: int,
        index: int,
        accepted: bool,
        reason: str,
        metadata: dict[str, Any],
    ) -> None:
        logger.info(
            "provider_candidate_decision",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "status": status,
                "endpoint": self.endpoint,
                "overpass_query": query,
                "candidate_index": index,
                "accepted": accepted,
                "reason": reason,
                **metadata,
            },
        )

    def _from_osm(self, item: dict[str, Any], payload: dict[str, Any]) -> RawBusiness:
        tags = item.get("tags") if isinstance(item.get("tags"), dict) else {}
        website = normalize_url(tags.get("website") or tags.get("contact:website"))
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        email = tags.get("email") or tags.get("contact:email")
        osm_type = item.get("type", "node")
        osm_id = item.get("id", "")
        source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_id else ""
        address = self._address_from_tags(tags, payload)
        return RawBusiness(
            name=(
                tags.get("name")
                or tags.get("brand")
                or tags.get("operator")
                or payload.get("query", "")
            ),
            industry=payload.get("category", payload.get("query", "Unknown")),
            website=website,
            phone=phone,
            email=email,
            country=payload.get("country") or tags.get("addr:country", ""),
            state=payload.get("state") or tags.get("addr:state", ""),
            city=payload.get("city") or tags.get("addr:city") or tags.get("addr:town") or "",
            address=address,
            description=(
                tags.get("description")
                or tags.get("amenity")
                or tags.get("tourism")
                or tags.get("shop")
            ),
            source_type="directory",
            source_url=source_url or "https://www.openstreetmap.org",
            trust_tier="C",
            confidence_score=65,
            contacts=[
                RawContact(
                    full_name="Public Contact",
                    role="General Contact",
                    email=email,
                    phone=phone,
                    source_url=website or "https://www.openstreetmap.org",
                )
            ]
            if email or phone
            else [],
            social_profiles=[],
        )

    def _tags_for_payload(self, payload: dict[str, Any]) -> tuple[tuple[str, str], ...]:
        candidates = [payload.get("category"), payload.get("query")]
        for candidate in candidates:
            key = self._category_key(candidate)
            if key in self.category_tags:
                return self.category_tags[key]
        raise ProviderError(
            "UNSUPPORTED_CATEGORY",
            "OpenStreetMap provider does not have an OSM tag mapping for this category.",
            False,
            self.name,
        )

    def _build_overpass_query(
        self,
        payload: dict[str, Any],
        tags: tuple[tuple[str, str], ...],
    ) -> tuple[str, str]:
        limit = max(1, min(int(payload.get("limit", 10)), 50))
        timeout = self._overpass_timeout_seconds()
        bbox = self._bbox_for_payload(payload)
        if bbox:
            south, west, north, east = bbox
            elements = self._element_queries_for_bbox(tags, south, west, north, east)
            return (
                "\n".join(
                    [
                        f"[out:json][timeout:{timeout}];",
                        "(",
                        *elements,
                        ");",
                        f"out center {limit};",
                    ]
                ),
                "bbox",
            )

        area_filters = self._area_filters(payload)
        elements = self._element_queries_for_area(tags)
        return (
            "\n".join(
                [
                    f"[out:json][timeout:{timeout}];",
                    *area_filters,
                    "(",
                    *elements,
                    ");",
                    f"out center {limit};",
                ]
            ),
            "area",
        )

    def _element_queries_for_bbox(
        self,
        tags: tuple[tuple[str, str], ...],
        south: float,
        west: float,
        north: float,
        east: float,
    ) -> list[str]:
        bounds = f"({south},{west},{north},{east})"
        return [
            f"  {element_type}{self._overpass_tag_selector(tag_key, tag_value)}{bounds};"
            for tag_key, tag_value in tags
            for element_type in ("node", "way", "relation")
        ]

    def _element_queries_for_area(self, tags: tuple[tuple[str, str], ...]) -> list[str]:
        return [
            f"  {element_type}{self._overpass_tag_selector(tag_key, tag_value)}(area.searchArea);"
            for tag_key, tag_value in tags
            for element_type in ("node", "way", "relation")
        ]

    def _overpass_timeout_seconds(self) -> int:
        if self.timeout_seconds <= 5:
            return max(1, self.timeout_seconds)
        return max(5, min(self.timeout_seconds - 5, 50))

    def _bbox_for_payload(
        self, payload: dict[str, Any]
    ) -> tuple[float, float, float, float] | None:
        country, state, city = self._location_parts(payload)
        key = (
            self._location_key(country),
            self._location_key(state),
            self._location_key(city),
        )
        return self.city_bounding_boxes.get(key)

    def _area_filters(self, payload: dict[str, Any]) -> list[str]:
        country, state, city = self._location_parts(payload)
        lines: list[str] = []
        if country:
            lines.append(
                f'area["boundary"="administrative"]["name"="{self._escape_overpass(country)}"]'
                "->.countryArea;"
            )
        if state:
            parent = "(area.countryArea)" if country else ""
            lines.append(
                f'area["boundary"="administrative"]["name"="{self._escape_overpass(state)}"]'
                f"{parent}->.regionArea;"
            )
        if city:
            parent = "(area.regionArea)" if state else "(area.countryArea)" if country else ""
            lines.append(
                f'area["boundary"="administrative"]["name"="{self._escape_overpass(city)}"]'
                f"{parent}->.searchArea;"
            )
        elif state:
            lines.append(".regionArea->.searchArea;")
        elif country:
            lines.append(".countryArea->.searchArea;")
        else:
            raise ProviderError(
                "INVALID_PROVIDER_QUERY",
                "OpenStreetMap provider requires a city, state, or country search area.",
                False,
                self.name,
            )
        return lines

    def _location_parts(self, payload: dict[str, Any]) -> tuple[str, str, str]:
        location_parts = [
            part.strip() for part in str(payload.get("location") or "").split(",") if part.strip()
        ]
        country = str(payload.get("country") or "").strip()
        state = str(payload.get("state") or "").strip()
        city = str(payload.get("city") or "").strip()
        if not city and location_parts:
            city = location_parts[0]
        if not state and len(location_parts) >= 2:
            state = location_parts[1]
        if not country and len(location_parts) >= 3:
            country = location_parts[-1]
        return country, state, city

    def _address_from_tags(self, tags: dict[str, Any], payload: dict[str, Any]) -> str:
        street = " ".join(
            part
            for part in (
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
            )
            if part
        )
        locality = ", ".join(
            part
            for part in (
                tags.get("addr:city") or tags.get("addr:town") or payload.get("city"),
                tags.get("addr:state") or payload.get("state"),
                tags.get("addr:country") or payload.get("country"),
            )
            if part
        )
        return ", ".join(part for part in (street, locality) if part) or payload.get("location", "")

    def _location_key(self, value: Any) -> str:
        return " ".join(str(value or "").strip().lower().replace("_", " ").split())

    def _category_key(self, value: Any) -> str:
        return self._location_key(value)

    def _overpass_tag_selector(self, key: str, value: str) -> str:
        return f'["{self._escape_overpass(key)}"="{self._escape_overpass(value)}"]'

    def _escape_overpass(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')


class CompositeBusinessProvider:
    def __init__(self, providers: list[BusinessSearchProvider]) -> None:
        self.providers = providers

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        last_error: ProviderError | None = None
        for provider in self.providers:
            logger.info(
                "provider_selected",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": provider.name,
                },
            )
            try:
                businesses = await provider.search(payload)
            except ProviderError as exc:
                last_error = exc
                logger.warning(
                    "provider_failed",
                    extra={
                        "request_id": payload.get("request_id", "unknown"),
                        "provider": provider.name,
                        "error_code": exc.code,
                        "retryable": exc.retryable,
                        "failure_reason": exc.message,
                        "fallback_available": provider is not self.providers[-1],
                    },
                )
                continue
            logger.info(
                "provider_result",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": provider.name,
                    "businesses_returned": len(businesses),
                },
            )
            if businesses:
                return businesses
        if last_error is not None:
            raise last_error
        return []
