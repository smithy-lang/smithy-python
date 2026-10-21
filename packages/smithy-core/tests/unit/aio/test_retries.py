#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import gc
import sys
import threading
import time
import weakref
from collections.abc import Callable, Coroutine, Iterator
from copy import deepcopy
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smithy_core.aio.client import RequestPipeline
from smithy_core.aio.retries import (
    AsyncAdaptiveRetryStrategy,
    AsyncClientRateLimiter,
    AsyncRetryStrategyResolver,
    AsyncSimpleRetryStrategy,
    AsyncStandardRetryStrategy,
    AsyncTokenBucket,
)
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import (
    CubicCalculator,
    ExponentialRetryBackoffStrategy,
    RequestRateTracker,
    RetryStrategyOptions,
    StandardRetryQuota,
)
from smithy_core.retries import (
    ExponentialBackoffJitterType as EBJT,
)


@pytest.mark.parametrize("max_attempts", [2, 3, 10])
async def test_simple_retry_strategy(max_attempts: int) -> None:
    strategy = AsyncSimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=max_attempts,
    )
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


async def test_simple_retry_does_not_retry_unclassified() -> None:
    strategy = AsyncSimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=Exception()
        )


async def test_simple_retry_does_not_retry_when_safety_unknown() -> None:
    strategy = AsyncSimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(is_retry_safe=None)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


async def test_simple_retry_does_not_retry_unsafe() -> None:
    strategy = AsyncSimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(fault="client", is_retry_safe=False)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.parametrize("max_attempts", [2, 3, 10])
async def test_standard_retry_strategy(max_attempts: int) -> None:
    strategy = AsyncStandardRetryStrategy(max_attempts=max_attempts)
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


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
async def test_standard_retry_does_not_retry(error: Exception | CallError) -> None:
    strategy = AsyncStandardRetryStrategy()
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


async def test_standard_retry_after_within_bounds_is_honored() -> None:
    strategy = AsyncStandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        )
    )
    error = CallError(is_retry_safe=True, retry_after=3.0)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 3.0


async def test_standard_retry_after_floored_to_backoff() -> None:
    strategy = AsyncStandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        )
    )
    error = CallError(is_retry_safe=True, retry_after=0.5)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 1.0


async def test_standard_retry_after_capped_at_backoff_plus_max() -> None:
    strategy = AsyncStandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        )
    )
    error = CallError(is_retry_safe=True, retry_after=10.0)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 6.0


async def test_standard_non_throttling_uses_default_backoff_scale() -> None:
    strategy = AsyncStandardRetryStrategy()
    error = CallError(is_retry_safe=True, is_throttling_error=False)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    # The default non-throttling backoff has a 50ms base with full jitter.
    assert 0 <= token.retry_delay <= 0.05


async def test_standard_throttling_uses_throttling_backoff_scale() -> None:
    strategy = AsyncStandardRetryStrategy()
    error = CallError(is_retry_safe=True, is_throttling_error=True)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    # The default throttling backoff has a 1s base with full jitter.
    assert 0 <= token.retry_delay <= 1.0


async def test_standard_throttling_and_non_throttling_use_separate_strategies() -> None:
    strategy = AsyncStandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=0.05,
            jitter_type=EBJT.NONE,
        ),
        throttling_backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1,
            jitter_type=EBJT.NONE,
        ),
    )
    non_throttling_error = CallError(is_retry_safe=True, is_throttling_error=False)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=non_throttling_error
    )
    assert token.retry_delay == pytest.approx(0.05)  # type: ignore

    throttling_error = CallError(is_retry_safe=True, is_throttling_error=True)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=throttling_error
    )
    assert token.retry_delay == pytest.approx(1.0)  # type: ignore


async def test_quota_exhausted_error_carries_backoff_delay() -> None:
    strategy = AsyncStandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=0.05, jitter_type=EBJT.NONE
        ),
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert exc_info.value.retry_after == pytest.approx(0.05)  # type: ignore


async def test_quota_exhausted_error_carries_throttling_backoff_delay() -> None:
    strategy = AsyncStandardRetryStrategy(
        throttling_backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        ),
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    error = CallError(is_retry_safe=True, is_throttling_error=True)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert exc_info.value.retry_after == pytest.approx(1.0)  # type: ignore


async def test_max_attempts_error_has_no_retry_after() -> None:
    strategy = AsyncStandardRetryStrategy(
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=1,
    )
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert exc_info.value.retry_after is None


async def test_non_retryable_error_has_no_retry_after() -> None:
    strategy = AsyncStandardRetryStrategy(
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    error = CallError(fault="client", is_retry_safe=False)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert exc_info.value.retry_after is None


async def test_standard_retry_invalid_max_attempts() -> None:
    with pytest.raises(ValueError):
        AsyncStandardRetryStrategy(max_attempts=-1)


async def test_retry_strategy_resolver_none_returns_default() -> None:
    resolver = AsyncRetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert isinstance(strategy, AsyncStandardRetryStrategy)
    assert strategy.max_attempts == 3


async def test_retry_strategy_resolver_creates_different_strategies() -> None:
    resolver = AsyncRetryStrategyResolver()

    options1 = RetryStrategyOptions(max_attempts=3)
    options2 = RetryStrategyOptions(max_attempts=5)

    strategy1 = await resolver.resolve_retry_strategy(retry_strategy=options1)
    strategy2 = await resolver.resolve_retry_strategy(retry_strategy=options2)

    assert strategy1.max_attempts == 3
    assert strategy2.max_attempts == 5
    assert strategy1 is not strategy2


async def test_retry_strategy_resolver_caches_strategies() -> None:
    resolver = AsyncRetryStrategyResolver()

    strategy1 = await resolver.resolve_retry_strategy(retry_strategy=None)
    strategy2 = await resolver.resolve_retry_strategy(retry_strategy=None)
    options = RetryStrategyOptions(max_attempts=5)
    strategy3 = await resolver.resolve_retry_strategy(retry_strategy=options)
    strategy4 = await resolver.resolve_retry_strategy(retry_strategy=options)

    assert strategy1 is strategy2
    assert strategy3 is strategy4
    assert strategy1 is not strategy3


async def test_retry_strategy_resolver_cache_is_not_shared_across_resolvers() -> None:
    resolver = AsyncRetryStrategyResolver()
    options = RetryStrategyOptions(retry_mode="adaptive")
    strategy = await resolver.resolve_retry_strategy(retry_strategy=options)

    for _ in range(200):
        await AsyncRetryStrategyResolver().resolve_retry_strategy(
            retry_strategy=options
        )

    assert await resolver.resolve_retry_strategy(retry_strategy=options) is strategy


async def test_retry_strategy_resolver_strategies_are_freed_with_resolver() -> None:
    resolver = AsyncRetryStrategyResolver()
    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)
    strategy_ref = weakref.ref(strategy)

    del resolver, strategy
    gc.collect()

    assert strategy_ref() is None


async def test_retry_strategy_resolver_returns_existing_strategy() -> None:
    resolver = AsyncRetryStrategyResolver()
    provided_strategy = AsyncSimpleRetryStrategy(max_attempts=7)

    strategy = await resolver.resolve_retry_strategy(retry_strategy=provided_strategy)

    assert strategy is provided_strategy
    assert strategy.max_attempts == 7


async def test_retry_strategy_resolver_rejects_invalid_type() -> None:
    resolver = AsyncRetryStrategyResolver()

    with pytest.raises(
        TypeError,
        match="retry_strategy must be AsyncRetryStrategy, RetryStrategyOptions, or None",
    ):
        await resolver.resolve_retry_strategy(retry_strategy="invalid")  # type: ignore


async def test_retry_strategy_resolver_uses_max_attempts_fallback() -> None:
    resolver = AsyncRetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=None, max_attempts=9
    )

    assert isinstance(strategy, AsyncStandardRetryStrategy)
    assert strategy.max_attempts == 9


async def test_retry_strategy_resolver_uses_retry_mode_fallback() -> None:
    resolver = AsyncRetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=None, retry_mode="simple", max_attempts=4
    )

    assert isinstance(strategy, AsyncSimpleRetryStrategy)
    assert strategy.max_attempts == 4


async def test_retry_strategy_resolver_uses_adaptive_retry_mode_fallback() -> None:
    resolver = AsyncRetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=None, retry_mode="adaptive", max_attempts=4
    )

    assert isinstance(strategy, AsyncAdaptiveRetryStrategy)
    assert strategy.max_attempts == 4


async def test_retry_strategy_resolver_fallback_defaults_when_unset() -> None:
    """Omitting both fallbacks must match the prior no-argument behavior."""
    resolver = AsyncRetryStrategyResolver()

    explicit = await resolver.resolve_retry_strategy(
        retry_strategy=None, retry_mode=None, max_attempts=None
    )
    baseline = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert explicit is baseline
    assert isinstance(explicit, AsyncStandardRetryStrategy)
    assert explicit.max_attempts == 3


async def test_explicit_retry_strategy_options_beat_fallbacks() -> None:
    resolver = AsyncRetryStrategyResolver()
    retry_strategy = RetryStrategyOptions(max_attempts=2)

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=retry_strategy, max_attempts=9
    )

    assert strategy.max_attempts == 2


async def test_explicit_retry_strategy_instance_beats_fallbacks() -> None:
    resolver = AsyncRetryStrategyResolver()
    provided = AsyncSimpleRetryStrategy(max_attempts=7)

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=provided, retry_mode="standard", max_attempts=9
    )

    assert strategy is provided
    assert strategy.max_attempts == 7


async def test_resolver_no_service_defaults_uses_strategy_defaults() -> None:
    resolver = AsyncRetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert isinstance(strategy, AsyncStandardRetryStrategy)
    assert strategy.max_attempts == 3
    delay = strategy.backoff_strategy.compute_next_backoff_delay(1)
    assert 0 <= delay <= 0.05
    throttling_delay = strategy.throttling_backoff_strategy.compute_next_backoff_delay(
        1
    )
    assert 0 <= throttling_delay <= 1.0


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_initial_state(self):
        token_bucket = AsyncTokenBucket()
        assert token_bucket.current_capacity == 0
        assert token_bucket.max_capacity == token_bucket.MIN_CAPACITY
        assert token_bucket.fill_rate == token_bucket.MIN_FILL_RATE

    @pytest.mark.asyncio
    async def test_acquire_succeeds_immediately_within_capacity(self):
        token_bucket = AsyncTokenBucket(curr_capacity=1)

        with patch("smithy_core.aio.retries.asyncio.wait_for") as mock_wait_for:
            await token_bucket.acquire(1)
            mock_wait_for.assert_not_called()

        assert token_bucket.current_capacity == 0

    @pytest.mark.asyncio
    async def test_acquire_waits_when_capacity_insufficient(self):
        token_bucket = AsyncTokenBucket(fill_rate=100.0)
        await token_bucket.acquire(1)

        with patch(
            "smithy_core.aio.retries.asyncio.wait_for", wraps=asyncio.wait_for
        ) as mock_wait_for:
            await token_bucket.acquire(1)
            mock_wait_for.assert_called()

        assert token_bucket.current_capacity == 0.0

    @pytest.mark.asyncio
    async def test_update_bucket_updates_rate(self):
        token_bucket = AsyncTokenBucket(curr_capacity=1)

        await token_bucket.update_rate(5.0)
        assert token_bucket.fill_rate == 5.0
        assert token_bucket.max_capacity == 5.0
        assert token_bucket.current_capacity == 1.0

    @pytest.mark.asyncio
    async def test_rate_can_never_be_zero(self):
        token_bucket = AsyncTokenBucket()
        await token_bucket.update_rate(0.0)

        assert token_bucket.fill_rate == AsyncTokenBucket.MIN_FILL_RATE
        assert token_bucket.max_capacity == AsyncTokenBucket.MIN_CAPACITY

    @pytest.mark.asyncio
    async def test_refill_caps_at_max_capacity(self):
        # 100s at 4 tokens/s would refill 400 tokens, far more than the capacity of 4
        with patch("time.monotonic", side_effect=[0.0, 0.0, 100.0]):
            token_bucket = AsyncTokenBucket()
            await token_bucket.update_rate(4.0)
            with token_bucket._lock:  # type: ignore
                token_bucket._refill()  # type: ignore

        assert token_bucket.current_capacity == 4.0

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
            token_bucket = AsyncTokenBucket(curr_capacity=0, fill_rate=2.0)

            for action, value in actions:
                if action == "acquire":
                    await token_bucket.acquire(value)
                elif action == "update":
                    await token_bucket.update_rate(value)

            assert token_bucket.current_capacity == expected_capacity

    async def test_update_rate_wakes_waiting_acquirers(self):
        token_bucket = AsyncTokenBucket(fill_rate=0.01)

        acquired = False

        async def slow_acquire():
            nonlocal acquired
            await token_bucket.acquire(2.0)
            acquired = True

        task = asyncio.create_task(slow_acquire())

        # Let slow_acquire() start waiting
        await asyncio.sleep(0.05)
        assert not acquired

        await token_bucket.update_rate(100.0)
        await asyncio.sleep(0.1)
        assert acquired
        await task

    async def test_acquire_does_not_wait_past_timeout(self):
        # The bucket starts empty, and at the minimum fill rate a token takes 2s to
        # refill, far past the timeout
        token_bucket = AsyncTokenBucket(timeout=0.05)

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            await token_bucket.acquire(1)
        assert time.monotonic() - start < 1

    def test_acquire_works_across_event_loops(self):
        # A client, and so its bucket, can outlive the event loop it was first used on
        token_bucket = AsyncTokenBucket(fill_rate=20.0)

        async def contended_acquires():
            # The bucket starts empty, so both acquires have to wait
            await asyncio.gather(token_bucket.acquire(1), token_bucket.acquire(1))

        asyncio.run(contended_acquires())
        asyncio.run(contended_acquires())


class TestSharedAcrossThreads:
    """One client, and so one rate limiter, may be used from several threads at once,
    each running its own event loop."""

    _THREADS = 8

    @pytest.fixture
    def frequent_thread_switches(self) -> Iterator[None]:
        # Switch threads constantly so they collide inside the critical sections
        original = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        yield
        sys.setswitchinterval(original)

    def _run_in_threads(
        self, target: Callable[[], Coroutine[Any, Any, None]]
    ) -> list[BaseException]:
        errors: list[BaseException] = []

        def run() -> None:
            try:
                asyncio.run(target())
            except BaseException as e:
                errors.append(e)

        threads = [
            threading.Thread(target=run, daemon=True) for _ in range(self._THREADS)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            # A deadlock fails the test instead of hanging the suite
            thread.join(timeout=30)
            assert not thread.is_alive(), "thread did not finish"
        return errors

    def test_rate_tracker(self, frequent_thread_switches: None):
        tracker = RequestRateTracker()

        async def measure_many() -> None:
            for _ in range(3000):
                tracker.measure_rate()

        assert self._run_in_threads(measure_many) == []

    def test_token_bucket_rate_updates_and_acquires(
        self, frequent_thread_switches: None
    ):
        bucket = AsyncTokenBucket(fill_rate=100000.0)

        async def update_and_acquire() -> None:
            await bucket.update_rate(100000.0)
            for _ in range(500):
                await bucket.acquire(1)
                assert bucket.current_capacity >= 0

        assert self._run_in_threads(update_and_acquire) == []

    def test_token_bucket_hands_out_each_token_once(
        self, frequent_thread_switches: None
    ):
        acquires_per_thread = 500
        # Exactly enough tokens for every acquire, so no thread has to wait
        bucket = AsyncTokenBucket(curr_capacity=self._THREADS * acquires_per_thread)

        async def spend() -> None:
            for _ in range(acquires_per_thread):
                await bucket.acquire(1)

        assert self._run_in_threads(spend) == []
        # A lost update to the count would leave tokens behind
        assert bucket.current_capacity < 1


class TestRateLimiter:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rate_limiter_enabled, current_bucket_capacity, expected_bucket_capacity_after_acquire",
        [
            (True, 2.0, 1.0),
            (False, 1.0, 1.0),
        ],
    )
    async def test_token_consumption_before_request_scenarios(
        self,
        rate_limiter_enabled: bool,
        current_bucket_capacity: float,
        expected_bucket_capacity_after_acquire: float,
    ):
        token_bucket = AsyncTokenBucket(curr_capacity=current_bucket_capacity)
        calculator = CubicCalculator(starting_max_rate=1.0, start_time=0.0)
        tracker = RequestRateTracker()

        limiter = AsyncClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=calculator,
            rate_tracker=tracker,
            rate_limiter_enabled=rate_limiter_enabled,
        )

        await limiter.before_sending_request()
        assert token_bucket.current_capacity == expected_bucket_capacity_after_acquire

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "throttling_error, rate_limiter_enabled, measured_rate, expected_bucket_fill_rate",
        [
            (True, False, 5.0, 3.5),
            (True, True, 5.0, 0.5),
            (False, True, 5.0, 7.83),
            (False, False, 5.0, 7.83),
        ],
    )
    async def test_token_consumption_after_response_scenarios(
        self,
        throttling_error: bool,
        rate_limiter_enabled: bool,
        measured_rate: float,
        expected_bucket_fill_rate: float,
    ):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3]
            token_bucket = AsyncTokenBucket()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            tracker = RequestRateTracker()

            limiter = AsyncClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=rate_limiter_enabled,
            )

            with patch.object(tracker, "measure_rate", return_value=measured_rate):
                await limiter.after_receiving_response(
                    throttling_error=throttling_error
                )

        assert round(token_bucket.fill_rate, 2) == expected_bucket_fill_rate

    async def test_throttling_response_enables_rate_limiter(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4]
            token_bucket = AsyncTokenBucket()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            tracker = RequestRateTracker()

            limiter = AsyncClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=False,
            )

            await limiter.after_receiving_response(throttling_error=True)
        assert limiter.rate_limit_enabled is True

    async def test_raises_timeout_error_when_token_acquisition_takes_30_secs(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 31]
            token_bucket = AsyncTokenBucket(curr_capacity=1)
            calculator = CubicCalculator()
            tracker = RequestRateTracker()
            limiter = AsyncClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=True,
            )

            await limiter.before_sending_request()
            with pytest.raises(TimeoutError):
                await limiter.before_sending_request()

    async def test_tokens_accumulation_after_numerous_successful_responses(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [i * 0.01 for i in range(5000)]
            token_bucket = AsyncTokenBucket(curr_capacity=1)
            calculator = CubicCalculator()
            tracker = RequestRateTracker()
            limiter = AsyncClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=True,
            )

            await limiter.after_receiving_response(throttling_error=True)
            for _ in range(1000):
                await limiter.after_receiving_response(throttling_error=False)
            await limiter.after_receiving_response(throttling_error=True)

            # The final throttle caps the tokens saved up during the successes
            assert token_bucket.current_capacity < 25

    async def test_sending_rate_sequence(self):
        # Each step is (throttled, timestamp, expected measured rate, expected fill
        # rate of the bucket)
        steps = [
            (False, 0.2, 0.0, 0.5),
            (False, 0.4, 0.0, 0.5),
            (False, 0.6, 4.8, 0.5),
            (False, 0.8, 4.8, 0.5),
            (False, 1.0, 4.16, 0.5),
            (False, 1.2, 4.16, 0.6912),
            (False, 1.4, 4.16, 1.0976),
            (False, 1.6, 5.632, 1.6384),
            (False, 1.8, 5.632, 2.3328),
            (True, 2.0, 4.3264, 3.02848),
            (False, 2.2, 4.3264, 3.486639),
            (False, 2.4, 4.3264, 3.821874),
            (False, 2.6, 5.66528, 4.053386),
            (False, 2.8, 5.66528, 4.200373),
            (False, 3.0, 4.333056, 4.282037),
            (True, 3.2, 4.333056, 2.997426),
            (False, 3.4, 4.333056, 3.452226),
        ]
        now = 0.0
        with (
            patch(
                "smithy_core.aio.retries.time", SimpleNamespace(monotonic=lambda: now)
            ),
            patch("smithy_core.retries.time", SimpleNamespace(monotonic=lambda: now)),
        ):
            token_bucket = AsyncTokenBucket()
            tracker = RequestRateTracker()
            limiter = AsyncClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=CubicCalculator(start_time=0.0),
                rate_tracker=tracker,
                rate_limiter_enabled=False,
            )

            for throttled, timestamp, measured_rate, fill_rate in steps:
                now = timestamp
                await limiter.after_receiving_response(throttling_error=throttled)

                assert tracker.measured_client_rate == pytest.approx(  # type: ignore
                    measured_rate, abs=1e-6
                )
                assert token_bucket.fill_rate == pytest.approx(fill_rate, abs=1e-6)  # type: ignore

    async def test_calculated_rate_is_capped_at_2x_measured_rate(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4]
            token_bucket = AsyncTokenBucket()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            tracker = RequestRateTracker()

            limiter = AsyncClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=True,
            )

            with (
                patch.object(tracker, "measure_rate", return_value=5.0),
                patch.object(
                    calculator, "calculate_scaled_request_rate", return_value=20.0
                ),
                patch.object(token_bucket, "_set_rate") as mock_set_rate,
            ):
                await limiter.after_receiving_response(throttling_error=False)

                # calculated rate should be capped at 2x measured rate at 2 * 5.0 = 10.0
                mock_set_rate.assert_called_once_with(10.0)

    async def test_new_rate_is_set_while_holding_the_lock(self):
        # Two threads could otherwise calculate rates A then B but apply B then A
        token_bucket = AsyncTokenBucket()
        limiter = AsyncClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=CubicCalculator(),
            rate_tracker=RequestRateTracker(),
            rate_limiter_enabled=True,
        )
        lock_held: list[bool] = []

        def record_lock(rate: float) -> None:
            lock_held.append(limiter._lock.locked())  # type: ignore[reportPrivateUsage]

        token_bucket._set_rate = record_lock  # type: ignore[method-assign]
        await limiter.after_receiving_response(throttling_error=True)
        await limiter.after_receiving_response(throttling_error=False)

        assert lock_held == [True, True]


class TestCubicCalculator:
    def test_cubic_calculator_initializes(self):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        assert calculator.last_max_rate == 10.0
        assert calculator.last_throttle_time == 5.0

    def test_calculate_inflection_point(self):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        time_window = calculator.calculate_and_update_inflection_point()
        assert round(time_window, 2) == 1.96

    @pytest.mark.parametrize(
        "cases",
        [
            # (response, timestamp, calculated_rate)
            [
                ("success", 5, 7.0),
                ("success", 6, 9.64893600966),
                ("success", 7, 10.000030849917364),
                ("success", 8, 10.453284520772092),
                ("success", 9, 13.408697022224185),
                ("success", 10, 21.26626835427364),
                ("success", 11, 36.425998516920465),
            ],
            [
                ("success", 5, 7.0),
                ("success", 6, 9.64893600966),
                ("throttle", 7, 6.754255206761999),
                ("throttle", 8, 4.727978644733399),
                ("success", 9, 6.606547753887045),
                ("success", 10, 6.763279816944947),
                ("success", 11, 7.598174833907107),
                ("success", 12, 11.511232804773524),
            ],
        ],
        ids=["successes", "successes_and_throttles"],
    )
    def test_rate_sequence_after_successes_and_throttles(
        self, cases: list[tuple[str, float, float]]
    ):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        current_rate = 10.0
        for response, timestamp, expected in cases:
            if response == "success":
                current_rate = calculator.calculate_scaled_request_rate(timestamp)
            else:
                current_rate = calculator.calculate_throttled_request_rate(
                    current_rate, timestamp
                )
            assert current_rate == pytest.approx(expected)  # type: ignore

    def test_throttle_request(self):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        result = calculator.calculate_throttled_request_rate(
            rate_to_use=8.0, timestamp=10.0
        )

        assert result == 8.0 * 0.7
        assert calculator.last_max_rate == 8.0
        assert calculator.last_throttle_time == 10.0


class TestRequestRateTracker:
    async def test_measure_rate_same_bucket(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.3, 0.4]
            tracker = RequestRateTracker()
            rate1 = tracker.measure_rate()
            rate2 = tracker.measure_rate()

        assert rate1 == 0
        assert rate2 == 0
        assert tracker.request_count == 2

    async def test_measure_rate_new_bucket(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.7]
            tracker = RequestRateTracker()

            tracker.measure_rate()
            rate = tracker.measure_rate()

            # 2 requests over a 0.5s bucket is 4 r/s, smoothed: 4 * 0.8 + 0 * 0.2
            assert rate == pytest.approx(3.2)  # type: ignore
            assert tracker.request_count == 0


class TestAdaptiveRetryStrategy:
    """Tests for AsyncAdaptiveRetryStrategy with rate limiting."""

    def test_initialization_with_default_rate_limiter(self):
        strategy = AsyncAdaptiveRetryStrategy()

        assert strategy.rate_limiter is not None
        assert isinstance(strategy.rate_limiter, AsyncClientRateLimiter)
        assert strategy.rate_limiter.rate_limit_enabled is False

    def test_initialization_with_custom_rate_limiter(self):
        token_bucket = AsyncTokenBucket()
        calculator = CubicCalculator(starting_max_rate=5.0, start_time=0.0)
        tracker = RequestRateTracker()
        custom_limiter = AsyncClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=calculator,
            rate_tracker=tracker,
            rate_limiter_enabled=True,
        )

        strategy = AsyncAdaptiveRetryStrategy(rate_limiter=custom_limiter)

        assert strategy.rate_limiter is custom_limiter
        assert strategy.rate_limiter.rate_limit_enabled is True

    @pytest.mark.parametrize(
        "error, expected",
        [
            (CallError(message="Throttled", is_throttling_error=True), True),
            (CallError(message="Server error", is_throttling_error=False), False),
            (Exception("Generic error"), False),
        ],
        ids=["throttling", "not_throttling", "not_a_call_error"],
    )
    def test_is_throttling_error(self, error: Exception, expected: bool):
        assert AsyncAdaptiveRetryStrategy().is_throttling_error(error) is expected

    @pytest.mark.asyncio
    async def test_resolver_creates_adaptive_strategy(self):
        resolver = AsyncRetryStrategyResolver()
        option1 = RetryStrategyOptions(retry_mode="adaptive")

        strategy = await resolver.resolve_retry_strategy(retry_strategy=option1)

        assert isinstance(strategy, AsyncAdaptiveRetryStrategy)
        assert strategy.max_attempts == 3

    @pytest.mark.parametrize("max_attempts", [2, 3, 10])
    async def test_adaptive_retry_strategy(self, max_attempts: int) -> None:
        strategy = AsyncAdaptiveRetryStrategy(max_attempts=max_attempts)
        error = CallError(is_retry_safe=True)
        token = await strategy.acquire_initial_retry_token()
        for _ in range(max_attempts - 1):
            token = await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    def test_deepcopy_returns_adaptive_strategy_with_rate_limiter(self) -> None:
        strategy = AsyncAdaptiveRetryStrategy()
        copied = deepcopy(strategy)

        assert copied is strategy
        assert isinstance(copied, AsyncAdaptiveRetryStrategy)
        assert copied.rate_limiter is strategy.rate_limiter


class TestRequestPipelineRateLimiting:
    def _non_retryable_call(self, strategy: AsyncAdaptiveRetryStrategy) -> Any:
        # A call whose input stream can't be resent, so it skips the retry loop
        call = MagicMock()
        call.retryable.return_value = False
        call.retry_strategy = strategy
        return call

    def _adaptive_strategy_with_mocked_limiter(
        self,
    ) -> tuple[AsyncAdaptiveRetryStrategy, AsyncClientRateLimiter]:
        limiter = AsyncClientRateLimiter(
            token_bucket=AsyncTokenBucket(),
            cubic_calculator=CubicCalculator(),
            rate_tracker=RequestRateTracker(),
            rate_limiter_enabled=True,
        )
        limiter.before_sending_request = AsyncMock()  # type: ignore[method-assign]
        limiter.after_receiving_response = AsyncMock()  # type: ignore[method-assign]
        return AsyncAdaptiveRetryStrategy(rate_limiter=limiter), limiter

    @pytest.mark.asyncio
    async def test_non_retryable_call_applies_rate_limiting_on_success(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        handle_attempt = AsyncMock(
            return_value=SimpleNamespace(transport_response=MagicMock(), response="ok")
        )

        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            await pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy), MagicMock(), None
            )

        handle_attempt.assert_awaited_once()
        limiter.before_sending_request.assert_awaited_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_awaited_once_with(  # type: ignore[attr-defined]
            throttling_error=False
        )

    @pytest.mark.asyncio
    async def test_non_retryable_call_reports_throttle_without_retrying(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        error = CallError(is_retry_safe=True, is_throttling_error=True)
        handle_attempt = AsyncMock(
            return_value=SimpleNamespace(transport_response=MagicMock(), response=error)
        )

        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            output_context = await pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy), MagicMock(), None
            )

        # Sent once and returned as-is, even though the error is retry-safe
        handle_attempt.assert_awaited_once()
        assert output_context.response is error
        limiter.before_sending_request.assert_awaited_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_awaited_once_with(True)  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_failure_without_response_does_not_update_rate_limiter(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        # Fails before sending, e.g. endpoint resolution or signing, so no response
        error = CallError(message="Unable to resolve endpoint", is_retry_safe=False)
        handle_attempt = AsyncMock(
            return_value=SimpleNamespace(transport_response=None, response=error)
        )

        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            output_context = await pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy), MagicMock(), None
            )

        assert output_context.response is error
        limiter.before_sending_request.assert_awaited_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_not_awaited()  # type: ignore[attr-defined]
