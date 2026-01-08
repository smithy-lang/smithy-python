#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from unittest.mock import patch

import pytest
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import ExponentialBackoffJitterType as EBJT
from smithy_core.retries import (
    ExponentialRetryBackoffStrategy,
    RetryStrategyOptions,
    RetryStrategyResolver,
    SimpleRetryStrategy,
    StandardRetryQuota,
    StandardRetryStrategy,
    TokenBucket,
)


@pytest.mark.parametrize(
    "jitter_type, scale_value, max_backoff, expected_delays",
    [
        # no jitter
        (EBJT.NONE, 2, 20, [0, 2.0, 4.0, 8.0, 16.0, 20.0, 20.0]),
        (EBJT.NONE, 2.0, 20.0, [0, 2.0, 4.0, 8.0, 16.0, 20.0, 20.0]),
        (EBJT.NONE, 1.0, 20.0, [0, 1.0, 2.0, 4.0, 8.0, 16.0, 20.0]),
        (EBJT.NONE, 4.0, 2.0, [0, 2.0, 2.0, 2.0]),
        (EBJT.NONE, 23.4, 76.5, [0, 23.4, 46.8, 76.5, 76.5]),
        # full jitter
        (EBJT.FULL, 2.0, 20.0, [0, 1.0, 2.0, 4.0, 8.0, 10.0, 10.0]),
        (EBJT.FULL, 5.0, 20.0, [0, 2.5, 5.0, 10.0, 10.0]),
        (EBJT.FULL, 5.0, 10.0, [0, 2.5, 5.0, 5.0, 5.0]),
        (EBJT.FULL, 23.4, 76.5, [0, 11.7, 23.4, 38.25, 38.25]),
        # equal jitter
        (EBJT.DEFAULT, 2.0, 20.0, [0, 1.5, 3.0, 6.0, 12.0, 15.0, 15.0]),
        (EBJT.DEFAULT, 23.4, 76.5, [0, 17.55, 35.1, 57.375, 57.375]),
        # decorrelated jitter
        (EBJT.DECORRELATED, 2.0, 20.0, [0, 5.0, 9.5, 16.25, 20.0, 20.0]),
        (EBJT.DECORRELATED, 23.4, 76.5, [0, 58.5, 76.5, 76.5]),
        # edge cases with zeros
        (EBJT.NONE, 5.0, 0.0, [0, 0, 0, 0]),
        (EBJT.NONE, 0.0, 5.0, [0, 0, 0, 0]),
        (EBJT.NONE, 0.0, 0.0, [0, 0, 0, 0]),
        (EBJT.FULL, 5.0, 0.0, [0, 0, 0, 0]),
        (EBJT.FULL, 0.0, 5.0, [0, 0, 0, 0]),
        (EBJT.FULL, 0.0, 0.0, [0, 0, 0, 0]),
    ],
)
def test_exponential_backoff_strategy(
    jitter_type: EBJT,
    scale_value: float,
    max_backoff: float,
    expected_delays: list[float],
) -> None:
    bos = ExponentialRetryBackoffStrategy(
        backoff_scale_value=scale_value,
        max_backoff=max_backoff,
        jitter_type=jitter_type,
        random=lambda: 0.5,  # every generated "random" value equals 0.5
    )

    for delay_index, delay_expected in enumerate(expected_delays):
        delay_actual = bos.compute_next_backoff_delay(retry_attempt=delay_index)
        assert delay_actual == pytest.approx(delay_expected)  # type: ignore


@pytest.mark.parametrize("max_attempts", [2, 3, 10])
def test_simple_retry_strategy(max_attempts: int) -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=max_attempts,
    )
    error = CallError(is_retry_safe=True)
    token = strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
    with pytest.raises(RetryError):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


def test_simple_retry_does_not_retry_unclassified() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    token = strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=Exception())


def test_simple_retry_does_not_retry_when_safety_unknown() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(is_retry_safe=None)
    token = strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


def test_simple_retry_does_not_retry_unsafe() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(fault="client", is_retry_safe=False)
    token = strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.parametrize("max_attempts", [2, 3, 10])
def test_standard_retry_strategy(max_attempts: int) -> None:
    strategy = StandardRetryStrategy(max_attempts=max_attempts)
    error = CallError(is_retry_safe=True)
    token = strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
    with pytest.raises(RetryError):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.parametrize(
    "error",
    [
        Exception(),
        CallError(is_retry_safe=None),
        CallError(fault="client", is_retry_safe=False),
    ],
    ids=[
        "unclassified_error",
        "safety_unknown_error",
        "unsafe_error",
    ],
)
def test_standard_retry_does_not_retry(error: Exception | CallError) -> None:
    strategy = StandardRetryStrategy()
    token = strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


def test_standard_retry_after_overrides_backoff() -> None:
    strategy = StandardRetryStrategy()
    error = CallError(is_retry_safe=True, retry_after=5.5)
    token = strategy.acquire_initial_retry_token()
    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert token.retry_delay == 5.5


def test_standard_retry_invalid_max_attempts() -> None:
    with pytest.raises(ValueError):
        StandardRetryStrategy(max_attempts=-1)


@pytest.fixture
def retry_quota() -> StandardRetryQuota:
    return StandardRetryQuota(initial_capacity=10)


def test_retry_quota_initial_state(
    retry_quota: StandardRetryQuota,
) -> None:
    assert retry_quota.available_capacity == 10


def test_retry_quota_acquire_success(
    retry_quota: StandardRetryQuota,
) -> None:
    acquired = retry_quota.acquire(error=Exception())
    assert retry_quota.available_capacity == 10 - acquired


def test_retry_quota_acquire_when_exhausted(
    retry_quota: StandardRetryQuota,
) -> None:
    # Drain capacity until insufficient for next acquire
    retry_quota.acquire(error=Exception())
    retry_quota.acquire(error=Exception())

    # Not enough capacity for another retry (need 5, only 0 left)
    with pytest.raises(RetryError, match="Retry quota exceeded"):
        retry_quota.acquire(error=Exception())


def test_retry_quota_release_restores_capacity(
    retry_quota: StandardRetryQuota,
) -> None:
    acquired = retry_quota.acquire(error=Exception())
    retry_quota.release(release_amount=acquired)
    assert retry_quota.available_capacity == 10


def test_retry_quota_release_zero_adds_increment(
    retry_quota: StandardRetryQuota,
) -> None:
    retry_quota.acquire(error=Exception())
    assert retry_quota.available_capacity == 5
    retry_quota.release(release_amount=0)
    assert retry_quota.available_capacity == 6


def test_retry_quota_release_caps_at_max(
    retry_quota: StandardRetryQuota,
) -> None:
    # Drain some capacity
    retry_quota.acquire(error=Exception())
    # Release more than we acquired. Should cap at initial capacity.
    retry_quota.release(release_amount=50)
    assert retry_quota.available_capacity == 10


def test_retry_quota_acquire_timeout_error(
    retry_quota: StandardRetryQuota,
) -> None:
    timeout_error = CallError(is_timeout_error=True, is_retry_safe=True)
    acquired = retry_quota.acquire(error=timeout_error)
    assert acquired == StandardRetryQuota.TIMEOUT_RETRY_COST
    assert retry_quota.available_capacity == 0


async def test_retry_strategy_resolver_none_returns_default() -> None:
    resolver = RetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 3


async def test_retry_strategy_resolver_creates_different_strategies() -> None:
    resolver = RetryStrategyResolver()

    options1 = RetryStrategyOptions(max_attempts=3)
    options2 = RetryStrategyOptions(max_attempts=5)

    strategy1 = await resolver.resolve_retry_strategy(retry_strategy=options1)
    strategy2 = await resolver.resolve_retry_strategy(retry_strategy=options2)

    assert strategy1.max_attempts == 3
    assert strategy2.max_attempts == 5
    assert strategy1 is not strategy2


async def test_retry_strategy_resolver_caches_strategies() -> None:
    resolver = RetryStrategyResolver()

    strategy1 = await resolver.resolve_retry_strategy(retry_strategy=None)
    strategy2 = await resolver.resolve_retry_strategy(retry_strategy=None)
    options = RetryStrategyOptions(max_attempts=5)
    strategy3 = await resolver.resolve_retry_strategy(retry_strategy=options)
    strategy4 = await resolver.resolve_retry_strategy(retry_strategy=options)

    assert strategy1 is strategy2
    assert strategy3 is strategy4
    assert strategy1 is not strategy3


async def test_retry_strategy_resolver_returns_existing_strategy() -> None:
    resolver = RetryStrategyResolver()
    provided_strategy = SimpleRetryStrategy(max_attempts=7)

    strategy = await resolver.resolve_retry_strategy(retry_strategy=provided_strategy)

    assert strategy is provided_strategy
    assert strategy.max_attempts == 7


async def test_retry_strategy_resolver_rejects_invalid_type() -> None:
    resolver = RetryStrategyResolver()

    with pytest.raises(
        TypeError,
        match="retry_strategy must be RetryStrategy, RetryStrategyOptions, or None",
    ):
        await resolver.resolve_retry_strategy(retry_strategy="invalid")  # type: ignore


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_initial_state(self):
        token_bucket = TokenBucket()
        assert token_bucket.current_capacity == token_bucket.MIN_CAPACITY
        assert token_bucket.max_capacity == token_bucket.MIN_CAPACITY
        assert token_bucket.fill_rate == token_bucket.MIN_FILL_RATE

    @pytest.mark.asyncio
    async def test_acquire_succeeds_immediately_within_capacity(self):
        token_bucket = TokenBucket()

        with patch("asyncio.sleep") as mock_sleep:
            await token_bucket.acquire(1)
            mock_sleep.assert_not_called()

        assert token_bucket.current_capacity == 0

    @pytest.mark.asyncio
    async def test_acquire_waits_when_capacity_insufficient(self):
        token_bucket = TokenBucket(fill_rate=1.0)
        await token_bucket.acquire(1)

        with patch("asyncio.sleep") as mock_sleep:
            await token_bucket.acquire(1)
            mock_sleep.assert_called()

        assert token_bucket.current_capacity == 0.0

    @pytest.mark.asyncio
    async def test_update_bucket_updates_rate(self):
        token_bucket = TokenBucket()

        await token_bucket.update_rate(5.0)
        assert token_bucket.fill_rate == 5.0
        assert token_bucket.max_capacity == 5.0
        assert token_bucket.current_capacity == 1.0

    @pytest.mark.asyncio
    async def test_rate_can_never_be_zero(self):
        token_bucket = TokenBucket()
        await token_bucket.update_rate(0.0)

        assert token_bucket.fill_rate != 0.0

    @pytest.mark.asyncio
    async def test_refill_caps_at_max_capacity(self):
        token_bucket = TokenBucket()
        # Max and current capacity of the bucket is set to 1.0 initially
        await token_bucket.update_rate(10.0)

        async with token_bucket._lock:  # type: ignore
            token_bucket._refill()  # type: ignore

        assert round(token_bucket.current_capacity, 1) == 1.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "actions,expected_capacity",
        [
            ([("acquire", 1)], 0.0),
            ([("acquire", 1), ("update", 4)], 1.0),
            ([("acquire", 1), ("update", 4), ("acquire", 1)], 3.0),
            ([("acquire", 1), ("update", 4), ("acquire", 1), ("acquire", 1)], 3.0),
        ],
    )
    async def test_multiple_refills_over_time(
        self, actions: list[tuple[str, int]], expected_capacity: float
    ):
        time_values = [0.0, 1.0, 1.0, 1.5, 1.5, 4.0, 4.0, 5.0]

        with patch("time.monotonic", side_effect=time_values):
            token_bucket = TokenBucket(curr_capacity=0, fill_rate=2.0)

            for action, value in actions:
                if action == "acquire":
                    await token_bucket.acquire(value)
                elif action == "update":
                    await token_bucket.update_rate(value)

            assert token_bucket.current_capacity == expected_capacity
