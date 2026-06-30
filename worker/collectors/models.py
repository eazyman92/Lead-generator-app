from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawContact:
    full_name: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    source_url: str = ""
    is_decision_maker: bool = False
    priority_score: int = 0


@dataclass(frozen=True)
class RawSocialProfile:
    platform: str
    url: str


@dataclass(frozen=True)
class RawBusiness:
    name: str
    industry: str
    website: str
    phone: str
    email: str | None
    country: str
    state: str
    city: str
    address: str
    description: str | None
    source_type: str
    source_url: str
    trust_tier: str
    confidence_score: int
    contacts: list[RawContact] = field(default_factory=list)
    social_profiles: list[RawSocialProfile] = field(default_factory=list)
