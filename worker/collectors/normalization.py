import re
from urllib.parse import urlparse, urlunparse

from collectors.models import RawBusiness, RawContact, RawSocialProfile


def normalize_whitespace(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def normalize_title(value: str | None) -> str:
    normalized = normalize_whitespace(value)
    return normalized.title() if normalized.isupper() or normalized.islower() else normalized


def normalize_url(value: str | None) -> str:
    value = normalize_whitespace(value)
    if not value:
        return ""
    if not value.lower().startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    path = parsed.path.rstrip("/") or ""
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            parsed.query,
            "",
        )
    )


def normalize_phone(value: str | None) -> str:
    value = normalize_whitespace(value)
    if not value:
        return ""
    prefix = "+" if value.startswith("+") else ""
    digits = re.sub(r"\D+", "", value)
    return f"{prefix}{digits}" if digits else ""


def normalize_email(value: str | None) -> str | None:
    value = normalize_whitespace(value).lower()
    return value or None


def deterministic_business_identity(business: RawBusiness) -> str:
    website = normalize_url(business.website)
    phone = normalize_phone(business.phone)
    if website:
        return f"website:{website}"
    if phone:
        return f"phone:{phone}"
    return "name-location:{name}:{country}:{state}:{city}".format(
        name=normalize_whitespace(business.name).lower(),
        country=normalize_whitespace(business.country).lower(),
        state=normalize_whitespace(business.state).lower(),
        city=normalize_whitespace(business.city).lower(),
    )


def normalize_business(business: RawBusiness) -> RawBusiness:
    return RawBusiness(
        name=normalize_title(business.name),
        industry=normalize_title(business.industry),
        website=normalize_url(business.website),
        phone=normalize_phone(business.phone),
        email=normalize_email(business.email),
        country=normalize_title(business.country),
        state=normalize_title(business.state),
        city=normalize_title(business.city),
        address=normalize_whitespace(business.address),
        description=normalize_whitespace(business.description) or None,
        source_type=normalize_whitespace(business.source_type) or "directory",
        source_url=normalize_url(business.source_url or business.website),
        trust_tier=business.trust_tier,
        confidence_score=max(0, min(int(business.confidence_score), 100)),
        contacts=[normalize_contact(contact) for contact in business.contacts],
        social_profiles=[normalize_social_profile(profile) for profile in business.social_profiles],
    )


def normalize_contact(contact: RawContact) -> RawContact:
    return RawContact(
        full_name=normalize_title(contact.full_name) or "Public Contact",
        role=normalize_title(contact.role) or None,
        email=normalize_email(contact.email),
        phone=normalize_phone(contact.phone) or None,
        linkedin_url=normalize_url(contact.linkedin_url) or None,
        source_url=normalize_url(contact.source_url),
        is_decision_maker=bool(contact.is_decision_maker),
        priority_score=max(0, min(int(contact.priority_score), 100)),
    )


def normalize_social_profile(profile: RawSocialProfile) -> RawSocialProfile:
    platform = normalize_whitespace(profile.platform).lower()
    if platform == "twitter":
        platform = "x"
    return RawSocialProfile(platform=platform, url=normalize_url(profile.url))
