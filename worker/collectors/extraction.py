import re
from html import unescape
from urllib.parse import urljoin

from collectors.models import RawContact, RawSocialProfile
from collectors.normalization import normalize_url

EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/company/[^\s\"'<>]+", re.I),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"'<>]+", re.I),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"'<>]+", re.I),
    "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/[^\s\"'<>]+", re.I),
    "x": re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[^\s\"'<>]+", re.I),
}


def strip_tags(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def role_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0].lower()
    if "sales" in local_part:
        return "Sales"
    if "procurement" in local_part or "purchasing" in local_part:
        return "Procurement"
    if "operations" in local_part or "ops" in local_part:
        return "Operations"
    if "manager" in local_part:
        return "Manager"
    if "director" in local_part:
        return "Director"
    if "ceo" in local_part or "chief" in local_part:
        return "CEO"
    if "owner" in local_part or "founder" in local_part:
        return "Owner"
    return "General Contact"


def contacts_from_public_html(html: str, source_url: str) -> list[RawContact]:
    text = strip_tags(html)
    emails = sorted(set(EMAIL_PATTERN.findall(text)))
    phones = sorted(set(match.strip() for match in PHONE_PATTERN.findall(text)))
    contacts: list[RawContact] = []
    for email in emails:
        contacts.append(
            RawContact(
                full_name="Public Contact",
                role=role_from_email(email),
                email=email,
                phone=phones[0] if phones else None,
                source_url=source_url,
            )
        )
    if not contacts and phones:
        contacts.append(
            RawContact(
                full_name="Public Contact",
                role="General Contact",
                phone=phones[0],
                source_url=source_url,
            )
        )
    return contacts


def social_profiles_from_public_html(html: str, source_url: str) -> list[RawSocialProfile]:
    profiles: list[RawSocialProfile] = []
    for platform, pattern in SOCIAL_PATTERNS.items():
        for match in sorted(set(pattern.findall(html))):
            profiles.append(
                RawSocialProfile(
                    platform=platform,
                    url=normalize_url(urljoin(source_url, match)),
                )
            )
    return profiles
