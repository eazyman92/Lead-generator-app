from jobs.retry import RetryPolicy


def test_retry_policy_uses_capped_exponential_backoff() -> None:
    policy = RetryPolicy(
        base_delay_seconds=5,
        max_delay_seconds=20,
        backoff_multiplier=2,
    )

    assert policy.delay_for_attempt(1) == 5
    assert policy.delay_for_attempt(2) == 10
    assert policy.delay_for_attempt(3) == 20
    assert policy.delay_for_attempt(4) == 20
