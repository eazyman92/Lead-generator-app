from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    base_delay_seconds: int
    max_delay_seconds: int
    backoff_multiplier: float

    def delay_for_attempt(self, attempt: int) -> int:
        """Return capped exponential retry delay for the current consumed attempt."""
        normalized_attempt = max(attempt, 1)
        delay = self.base_delay_seconds * (
            self.backoff_multiplier ** (normalized_attempt - 1)
        )
        return min(int(delay), self.max_delay_seconds)
