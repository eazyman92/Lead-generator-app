import asyncio
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


class OpenStreetMapBusinessProvider:
    """Public business discovery provider backed by OpenStreetMap Overpass."""

    name = "openstreetmap"
    endpoint = "https://overpass-api.de/api/interpreter"
    category_tags = {
        "accountants": ("office", "accountant"),
        "accounting": ("office", "accountant"),
        "atm": ("amenity", "atm"),
        "atms": ("amenity", "atm"),
        "bank": ("amenity", "bank"),
        "banks": ("amenity", "bank"),
        "bar": ("amenity", "bar"),
        "bars": ("amenity", "bar"),
        "cafe": ("amenity", "cafe"),
        "cafes": ("amenity", "cafe"),
        "clinic": ("amenity", "clinic"),
        "clinics": ("amenity", "clinic"),
        "dentist": ("amenity", "dentist"),
        "dentists": ("amenity", "dentist"),
        "doctors": ("amenity", "doctors"),
        "gym": ("leisure", "fitness_centre"),
        "gyms": ("leisure", "fitness_centre"),
        "hospital": ("amenity", "hospital"),
        "hospitals": ("amenity", "hospital"),
        "hotel": ("tourism", "hotel"),
        "hotels": ("tourism", "hotel"),
        "law firm": ("office", "lawyer"),
        "law firms": ("office", "lawyer"),
        "lawyer": ("office", "lawyer"),
        "lawyers": ("office", "lawyer"),
        "pharmacy": ("amenity", "pharmacy"),
        "pharmacies": ("amenity", "pharmacy"),
        "restaurant": ("amenity", "restaurant"),
        "restaurants": ("amenity", "restaurant"),
        "school": ("amenity", "school"),
        "schools": ("amenity", "school"),
        "supermarket": ("shop", "supermarket"),
        "supermarkets": ("shop", "supermarket"),
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

    def __init__(self, user_agent: str, timeout_seconds: int = 10) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        tag_key, tag_value = self._tag_for_payload(payload)
        query, search_mode = self._build_overpass_query(payload, tag_key, tag_value)
        limit = int(payload.get("limit", 10))
        logger.info(
            "provider_request",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "endpoint": self.endpoint,
                "overpass_query": query,
                "overpass_search_mode": search_mode,
                "osm_tag_key": tag_key,
                "osm_tag_value": tag_value,
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
        request = Request(
            self.endpoint,
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
                    "endpoint": self.endpoint,
                    "overpass_search_mode": search_mode,
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
                "endpoint": self.endpoint,
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
                "endpoint": self.endpoint,
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

    def _tag_for_payload(self, payload: dict[str, Any]) -> tuple[str, str]:
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
        tag_key: str,
        tag_value: str,
    ) -> tuple[str, str]:
        limit = max(1, min(int(payload.get("limit", 10)), 50))
        selector = self._overpass_tag_selector(tag_key, tag_value)
        timeout = self._overpass_timeout_seconds()
        bbox = self._bbox_for_payload(payload)
        if bbox:
            south, west, north, east = bbox
            return (
                "\n".join(
                    [
                        f"[out:json][timeout:{timeout}];",
                        "(",
                        f"  node{selector}({south},{west},{north},{east});",
                        f"  way{selector}({south},{west},{north},{east});",
                        f"  relation{selector}({south},{west},{north},{east});",
                        ");",
                        f"out center {limit};",
                    ]
                ),
                "bbox",
            )

        area_filters = self._area_filters(payload)
        return (
            "\n".join(
                [
                    f"[out:json][timeout:{timeout}];",
                    *area_filters,
                    "(",
                    f"  node{selector}(area.searchArea);",
                    f"  way{selector}(area.searchArea);",
                    f"  relation{selector}(area.searchArea);",
                    ");",
                    f"out center {limit};",
                ]
            ),
            "area",
        )

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
        for provider in self.providers:
            logger.info(
                "provider_selected",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": provider.name,
                },
            )
            businesses = await provider.search(payload)
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
        return []
