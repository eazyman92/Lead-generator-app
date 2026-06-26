import asyncio
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from collectors.extraction import contacts_from_public_html, social_profiles_from_public_html
from collectors.models import RawBusiness, RawSocialProfile
from collectors.normalization import normalize_business, normalize_url
from collectors.providers import (
    BusinessSearchProvider,
    CompositeBusinessProvider,
    OpenStreetMapBusinessProvider,
    PayloadBusinessProvider,
)
from jobs.models import HandlerResult, JobSnapshot

if TYPE_CHECKING:
    from collectors.repository import CollectorRepository
    from config.settings import Settings


class ContactCollectionError(Exception):
    def __init__(self, code: str, message: str, retryable: bool) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


@dataclass
class CollectionProgress:
    businesses_processed: int = 0
    contacts_found: int = 0
    contacts_saved: int = 0
    duplicates_skipped: int = 0
    errors: int = 0
    completion_percent: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "businesses_processed": self.businesses_processed,
            "contacts_found": self.contacts_found,
            "contacts_saved": self.contacts_saved,
            "duplicates_skipped": self.duplicates_skipped,
            "errors": self.errors,
            "completion_percent": self.completion_percent,
        }


class ContactCollectionService:
    def __init__(
        self,
        settings: "Settings",
        repository: "CollectorRepository",
        provider: BusinessSearchProvider,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.provider = provider

    async def run(self, job: JobSnapshot) -> CollectionProgress:
        async with self.repository.session_factory() as session:
            payload = await self.repository.load_job_payload(session, job.id)
            request_id = payload.get("request_id") or "system"
            user_id = payload.get("created_by_user_id")
            try:
                data = self._validate_payload(payload)
            except ContactCollectionError as exc:
                await self.repository.audit(
                    session,
                    "contact_collection_failed",
                    request_id,
                    user_id,
                    {"job_id": job.id, "failure_reason": exc.code},
                )
                await session.commit()
                raise
            user_id = data.get("user_id") or user_id
            progress = CollectionProgress()
            await self.repository.audit(
                session,
                "contact_collection_started",
                request_id,
                user_id,
                {"job_id": job.id},
            )
            await self.repository.audit(
                session,
                "search_started",
                request_id,
                user_id,
                {
                    "job_id": job.id,
                    "query": data.get("query"),
                    "location": data.get("location"),
                    "category": data.get("category"),
                },
            )

            try:
                raw_businesses = await self.provider.search(data)
            except (TimeoutError, URLError) as exc:
                raise ContactCollectionError(
                    "PROVIDER_FAILURE",
                    "Business search provider failed.",
                    True,
                ) from exc
            except Exception as exc:
                raise ContactCollectionError(
                    "PROVIDER_FAILURE",
                    "Business search provider failed.",
                    True,
                ) from exc

            businesses = [normalize_business(item) for item in raw_businesses]
            total = max(len(businesses), 1)
            for business in businesses:
                try:
                    await self._process_business(session, business, request_id, user_id, progress)
                except Exception:
                    progress.errors += 1
                    await self.repository.audit(
                        session,
                        "contact_collection_failed",
                        request_id,
                        user_id,
                        {"job_id": job.id, "business_name": business.name},
                    )
                progress.businesses_processed += 1
                progress.completion_percent = int((progress.businesses_processed / total) * 100)
                await self.repository.update_progress(session, job.id, progress.as_dict())
                await self.repository.audit(
                    session,
                    "job_progress_updated",
                    request_id,
                    user_id,
                    {"job_id": job.id, **progress.as_dict()},
                )

            await self.repository.audit(
                session,
                "contact_collection_completed",
                request_id,
                user_id,
                {"job_id": job.id, **progress.as_dict()},
            )
            await self.repository.update_progress(
                session,
                job.id,
                {**progress.as_dict(), "completion_percent": 100},
            )
            await self.repository.audit(
                session,
                "job_completed",
                request_id,
                user_id,
                {"job_id": job.id, **progress.as_dict()},
            )
            await session.commit()
            return progress

    async def _process_business(
        self,
        session,
        business: RawBusiness,
        request_id: str,
        user_id: str | None,
        progress: CollectionProgress,
    ) -> None:
        await self.repository.audit(
            session,
            "business_found",
            request_id,
            user_id,
            {"business_name": business.name, "source_url": business.source_url},
        )
        business_id, created = await self.repository.save_business(session, business)
        await self.repository.audit(
            session,
            "business_saved" if created else "business_updated",
            request_id,
            user_id,
            {"business_id": str(business_id), "business_name": business.name},
        )
        source_id = await self.repository.save_data_source(session, business_id, business)
        await self.repository.audit(
            session,
            "data_source_recorded",
            request_id,
            user_id,
            {"business_id": str(business_id), "source_id": str(source_id)},
        )

        contacts = list(business.contacts)
        social_profiles = list(business.social_profiles)
        if business.website:
            social_profiles.append(RawSocialProfile(platform="website", url=business.website))
        for source_url in self._source_urls(business):
            try:
                fetched_contacts, fetched_profiles = await self._extract_from_source(source_url)
            except ContactCollectionError as exc:
                progress.errors += 1
                await self.repository.audit(
                    session,
                    "contact_collection_source_failed",
                    request_id,
                    user_id,
                    {
                        "business_id": str(business_id),
                        "source_url": source_url,
                        "failure_reason": exc.code,
                        "retryable": exc.retryable,
                    },
                )
                continue
            contacts.extend(fetched_contacts)
            social_profiles.extend(fetched_profiles)

        for contact in contacts:
            if not contact.source_url:
                contact = replace(contact, source_url=business.source_url or business.website)
            progress.contacts_found += 1
            await self.repository.audit(
                session,
                "contact_found",
                request_id,
                user_id,
                {
                    "business_id": str(business_id),
                    "email_present": bool(contact.email),
                    "phone_present": bool(contact.phone),
                    "source_url": contact.source_url,
                },
            )
            contact_id, inserted = await self.repository.save_contact(
                session,
                business_id,
                source_id,
                contact,
            )
            if inserted:
                progress.contacts_saved += 1
                event_type = "contact_saved"
            else:
                progress.duplicates_skipped += 1
                event_type = "contact_updated"
            await self.repository.audit(
                session,
                event_type,
                request_id,
                user_id,
                {"business_id": str(business_id), "contact_id": str(contact_id)},
            )

        for profile in social_profiles:
            profile_id, inserted = await self.repository.save_social_profile(
                session,
                business_id,
                profile,
            )
            if inserted and profile_id is not None:
                await self.repository.audit(
                    session,
                    "social_profile_saved",
                    request_id,
                    user_id,
                    {"business_id": str(business_id), "social_profile_id": str(profile_id)},
                )

    async def _extract_from_source(self, source_url: str):
        source_url = normalize_url(source_url)
        if not source_url:
            return [], []
        try:
            html = await asyncio.to_thread(self._fetch_public_html, source_url)
        except HTTPError as exc:
            if exc.code in {401}:
                raise ContactCollectionError(
                    "SOURCE_AUTH_REQUIRED",
                    "Source requires auth.",
                    False,
                ) from exc
            if exc.code in {403}:
                raise ContactCollectionError(
                    "SOURCE_FORBIDDEN",
                    "Source forbids access.",
                    False,
                ) from exc
            if exc.code == 429:
                raise ContactCollectionError(
                    "HTTP_429",
                    "Source rate limited request.",
                    True,
                ) from exc
            if exc.code >= 500:
                raise ContactCollectionError("HTTP_5XX", "Source server error.", True) from exc
            return [], []
        except TimeoutError as exc:
            raise ContactCollectionError(
                "NETWORK_TIMEOUT",
                "Source request timed out.",
                True,
            ) from exc
        except URLError as exc:
            raise ContactCollectionError(
                "DNS_FAILURE",
                "Source could not be resolved.",
                True,
            ) from exc
        return contacts_from_public_html(html, source_url), social_profiles_from_public_html(
            html,
            source_url,
        )

    def _fetch_public_html(self, source_url: str) -> str:
        request = Request(source_url, headers={"User-Agent": self.settings.worker_user_agent})
        with urlopen(request, timeout=self.settings.worker_http_timeout_seconds) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                raise ContactCollectionError(
                    "UNSUPPORTED_CONTENT_TYPE",
                    "Source returned unsupported content.",
                    False,
                )
            return response.read(1_000_000).decode("utf-8", errors="ignore")

    def _source_urls(self, business: RawBusiness) -> list[str]:
        urls = [business.source_url, business.website]
        return [normalize_url(url) for url in urls if normalize_url(url)]

    def _validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload.get("data") or payload)
        data["idempotency_key"] = data.get("idempotency_key") or payload.get("idempotency_key")
        data["user_id"] = data.get("user_id") or payload.get("created_by_user_id")
        if "limit" in data:
            data["limit"] = max(
                1,
                min(int(data["limit"]), self.settings.contact_collection_max_limit),
            )
        else:
            data["limit"] = 10
        if data.get("businesses"):
            return data
        missing = [field for field in ("query", "location", "category") if not data.get(field)]
        if missing:
            raise ContactCollectionError(
                "INVALID_PAYLOAD",
                f"Missing required contact collection fields: {', '.join(missing)}.",
                False,
            )
        return data


class ContactCollectionHandler:
    def __init__(self, service: ContactCollectionService) -> None:
        self.service = service

    async def handle(self, job: JobSnapshot) -> HandlerResult:
        try:
            await self.service.run(job)
            return HandlerResult.completed()
        except ContactCollectionError as exc:
            return HandlerResult.failed(exc.code, exc.message, exc.retryable)
        except Exception as exc:
            return HandlerResult.failed("DB_CONFLICT", str(exc), True)


def build_contact_collection_handler(settings: "Settings") -> ContactCollectionHandler:
    from collectors.repository import CollectorRepository

    repository = CollectorRepository(settings.database_url)
    provider = CompositeBusinessProvider(
        [
            PayloadBusinessProvider(),
            OpenStreetMapBusinessProvider(
                settings.worker_user_agent,
                settings.worker_http_timeout_seconds,
            ),
        ]
    )
    return ContactCollectionHandler(ContactCollectionService(settings, repository, provider))
