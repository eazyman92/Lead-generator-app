from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.exceptions import RateLimitError


@dataclass(frozen=True)
class RateLimitRule:
    max_requests: int
    window: timedelta


class InMemoryRateLimiter:
    """Simple process-local rate limiter for V1 development enforcement."""

    def __init__(self) -> None:
        self._requests: dict[tuple[str, str], deque[datetime]] = defaultdict(deque)

    def check(self, user_id: UUID, scope: str, rule: RateLimitRule) -> None:
        """Record a request or raise when the rule is exceeded."""
        key = (str(user_id), scope)
        now = datetime.now(timezone.utc)
        cutoff = now - rule.window
        requests = self._requests[key]

        while requests and requests[0] <= cutoff:
            requests.popleft()

        if len(requests) >= rule.max_requests:
            raise RateLimitError()

        requests.append(now)

    def check_all(self, user_id: UUID, scope: str, rules: tuple[RateLimitRule, ...]) -> None:
        """Record one request after all configured rules pass."""
        key = (str(user_id), scope)
        now = datetime.now(timezone.utc)
        requests = self._requests[key]
        max_window = max(rule.window for rule in rules)
        cutoff = now - max_window

        while requests and requests[0] <= cutoff:
            requests.popleft()

        for rule in rules:
            rule_cutoff = now - rule.window
            active_requests = [request for request in requests if request > rule_cutoff]
            if len(active_requests) >= rule.max_requests:
                raise RateLimitError()

        requests.append(now)


SEARCH_RATE_LIMIT_RULES = (
    RateLimitRule(max_requests=60, window=timedelta(minutes=1)),
    RateLimitRule(max_requests=1000, window=timedelta(days=1)),
)
_rate_limiter = InMemoryRateLimiter()


def check_search_rate_limit(user_id: UUID, scope: str = "search") -> None:
    """Apply V1 per-user search-domain rate limits."""
    _rate_limiter.check_all(user_id, scope, SEARCH_RATE_LIMIT_RULES)
