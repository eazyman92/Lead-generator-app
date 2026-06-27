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
                    contact.get("source_url")
                    or item.get("source_url")
                    or item.get("website", "")
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
            item.get("source_url")
            or item.get("website")
            or root_payload.get("source_url", "")
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
    """Public business search provider backed by OpenStreetMap Nominatim."""

    name = "openstreetmap"

    def __init__(self, user_agent: str, timeout_seconds: int = 10) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    async def search(self, payload: dict[str, Any]) -> list[RawBusiness]:
        query = " ".join(
            value
            for value in (
                payload.get("query"),
                payload.get("category"),
                payload.get("location"),
            )
            if value
        )
        limit = int(payload.get("limit", 10))
        if not query:
            return []
        params = urlencode(
            {
                "format": "jsonv2",
                "q": query,
                "limit": max(1, min(limit, 50)),
                "addressdetails": 1,
                "extratags": 1,
            }
        )
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        logger.info(
            "provider_request",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "query": query,
                "limit": max(1, min(limit, 50)),
            },
        )
        return await asyncio.to_thread(self._search_sync, url, payload)

    def _search_sync(self, url: str, payload: dict[str, Any]) -> list[RawBusiness]:
        request = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            code = "HTTP_429" if exc.code == 429 else "HTTP_5XX" if exc.code >= 500 else "PROVIDER_FAILURE"
            logger.warning(
                "provider_response_failed",
                extra={
                    "request_id": payload.get("request_id", "unknown"),
                    "provider": self.name,
                    "status": exc.code,
                    "error_code": code,
                },
            )
            raise ProviderError(
                code,
                "Provider request failed.",
                exc.code == 429 or exc.code >= 500,
                self.name,
            ) from exc
        except TimeoutError as exc:
            raise ProviderError("NETWORK_TIMEOUT", "Provider request timed out.", True, self.name) from exc
        except URLError as exc:
            raise ProviderError("DNS_FAILURE", "Provider could not be resolved.", True, self.name) from exc

        try:
            results = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "INVALID_PROVIDER_RESPONSE",
                "Provider returned invalid JSON.",
                False,
                self.name,
            ) from exc
        if not isinstance(results, list):
            raise ProviderError(
                "INVALID_PROVIDER_RESPONSE",
                "Provider returned an invalid response shape.",
                False,
                self.name,
            )
        logger.info(
            "provider_response",
            extra={
                "request_id": payload.get("request_id", "unknown"),
                "provider": self.name,
                "status": status,
                "businesses_returned": len(results),
            },
        )
        return [self._from_osm(item, payload) for item in results]

    def _from_osm(self, item: dict[str, Any], payload: dict[str, Any]) -> RawBusiness:
        address = item.get("address", {})
        extratags = item.get("extratags", {})
        website = normalize_url(extratags.get("website") or extratags.get("contact:website"))
        phone = extratags.get("phone") or extratags.get("contact:phone") or ""
        email = extratags.get("email") or extratags.get("contact:email")
        display_name = item.get("display_name", "")
        osm_type = item.get("osm_type", "node")
        osm_id = item.get("osm_id", "")
        source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_id else ""
        return RawBusiness(
            name=item.get("name")
            or display_name.split(",", 1)[0]
            or payload.get("query", ""),
            industry=payload.get("category", payload.get("query", "Unknown")),
            website=website,
            phone=phone,
            email=email,
            country=payload.get("country") or address.get("country", ""),
            state=payload.get("state") or address.get("state", ""),
            city=(
                payload.get("city")
                or address.get("city")
                or address.get("town")
                or address.get("village")
                or ""
            ),
            address=display_name,
            description=item.get("type"),
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
