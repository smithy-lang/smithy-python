#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import weakref
from typing import Any, ClassVar

from ..interfaces import retries as retries_interface
from ..retries import (
    RetryStrategyOptions,
    RetryStrategyType,
    SimpleRetryToken,
    StandardRetryQuota,
    StandardRetryToken,
    _AdaptiveRetryStrategyBase,  # pyright: ignore[reportPrivateUsage]
    _ClientRateLimiterBase,  # pyright: ignore[reportPrivateUsage]
    _RequestRateTrackerBase,  # pyright: ignore[reportPrivateUsage]
    _RetryStrategyResolverBase,  # pyright: ignore[reportPrivateUsage]
    _SimpleRetryStrategyBase,  # pyright: ignore[reportPrivateUsage]
    _StandardRetryStrategyBase,  # pyright: ignore[reportPrivateUsage]
    _TokenBucketBase,  # pyright: ignore[reportPrivateUsage]
)
from .interfaces.retries import AsyncRetryStrategy

__all__ = [
    "AsyncAdaptiveRetryStrategy",
    "AsyncClientRateLimiter",
    "AsyncRequestRateTracker",
    "AsyncRetryStrategyResolver",
    "AsyncSimpleRetryStrategy",
    "AsyncStandardRetryStrategy",
    "AsyncTokenBucket",
]


class AsyncSimpleRetryStrategy(_SimpleRetryStrategyBase):
    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> SimpleRetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: This argument is ignored by this retry strategy.
        """
        return self._initial_token()

    async def refresh_retry_token_for_retry(
        self, *, token_to_renew: retries_interface.RetryToken, error: Exception
    ) -> SimpleRetryToken:
        """Replace an existing retry token from a failed attempt with a new token.

        This retry strategy always returns a token until the attempt count stored in
        the new token exceeds the ``max_attempts`` value.

        :param token_to_renew: The token used for the previous failed attempt.
        :param error: The error that triggered the need for a retry.
        :raises RetryError: If no further retry attempts are allowed.
        """
        return self._refresh_token(token_to_renew, error)

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        """Not used by this retry strategy."""


class AsyncStandardRetryStrategy(_StandardRetryStrategyBase):
    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> StandardRetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: This argument is ignored by this retry strategy.
        """
        return self._initial_token()

    async def refresh_retry_token_for_retry(
        self, *, token_to_renew: retries_interface.RetryToken, error: Exception
    ) -> StandardRetryToken:
        """Replace an existing retry token from a failed attempt with a new token.

        This retry strategy always returns a token until the attempt count stored in
        the new token exceeds the ``max_attempts`` value.

        :param token_to_renew: The token used for the previous failed attempt.
        :param error: The error that triggered the need for a retry.
        :raises RetryError: If no further retry attempts are allowed. When the retry
            quota is exhausted, the raised error carries ``retry_after`` so callers
            such as long-polling operations can back off before returning.
        """
        return self._refresh_token(token_to_renew, error)

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        """Release retry quota back based on the amount consumed by the last retry.

        :param token: The token used for the previous successful attempt.
        """
        self._release_quota(token)


class AsyncTokenBucket(_TokenBucketBase):
    """Token bucket for rate limiting with configurable fill rate.

    AsyncTokenBucket provides a collection of arbitrary tokens while managing issuance
    and refilling over time. This is controlled by a fill rate that can be variably
    adjusted. When tokens aren't available, the bucket will enforce a delay before
    attempting to reacquire tokens until one is available or the defined timeout is
    reached.

    The bucket is safe to share across threads, each running its own event loop. A
    threading.Lock guards the token count and rate, because an asyncio primitive only
    coordinates tasks on a single event loop. The lock only covers short arithmetic and
    is never held across an ``await``, so it never blocks for long. Waiting for tokens
    uses a per-event-loop asyncio.Condition and does not hold the lock.
    """

    def __init__(
        self,
        *,
        curr_capacity: float = 0,
        fill_rate: float = _TokenBucketBase.MIN_FILL_RATE,
        timeout: float = _TokenBucketBase.DEFAULT_TIMEOUT,
    ):
        """Initialize a new AsyncTokenBucket.

        :param curr_capacity: Initial number of tokens in the bucket. The bucket can
            hold at least MIN_CAPACITY tokens, but starts empty by default.
        :param fill_rate: Rate at which tokens are added to the bucket (tokens/second).
        :param timeout: Maximum time to wait for token acquisition before
        raising TimeoutError.
        """
        super().__init__(
            curr_capacity=curr_capacity, fill_rate=fill_rate, timeout=timeout
        )
        self._conditions: weakref.WeakKeyDictionary[
            asyncio.AbstractEventLoop, asyncio.Condition
        ] = weakref.WeakKeyDictionary()

    async def acquire(self, amount: float) -> None:
        """Acquire tokens from the bucket.

        If sufficient tokens are available, they are immediately consumed and the
        method returns. If insufficient tokens are available, the method will wait
        until enough tokens have been refilled or the timeout is reached.

        :param amount: Number of tokens to acquire.

        :raises TimeoutError: Acquisition took longer than the configured timeout.
        """
        start_time = self._monotonic()
        condition = self._get_condition()
        async with condition:
            while (wait := self._try_acquire(amount, start_time)) is not None:
                # Wait outside the thread lock
                try:
                    await asyncio.wait_for(condition.wait(), timeout=wait)
                except TimeoutError:
                    pass

    def _get_condition(self) -> asyncio.Condition:
        """Return the Condition for the event loop that is currently running.

        An asyncio.Condition belongs to the first event loop that waits on it, and
        using it from any other loop raises a RuntimeError. The bucket lives as long
        as the client, so it can outlive the loop it was first used on.

        For example, a client using the CRT HTTP client can be reused across
        separate asyncio.run() calls, such as one call per Lambda invocation. If a
        request waits for a token during the first call, the Condition is tied to
        that loop. Without this check, every request that has to wait for a token
        in a later asyncio.run() call would fail.

        To avoid that, each event loop gets its own Condition, which is reused for as
        long as that loop exists and is released along with it.
        """
        loop = asyncio.get_running_loop()
        with self._lock:
            condition = self._conditions.get(loop)
            if condition is None:
                condition = asyncio.Condition()
                self._conditions[loop] = condition
            return condition

    async def update_rate(self, rate: float) -> None:
        """Update the bucket's fill rate, maximum capacity and current capacity (if its
        greater than maximum capacity).

        :param rate: New fill rate (tokens/second). It won't be less than MIN_FILL_RATE.
            Current capacity will be reduced if it exceeds the new maximum capacity.
        """
        self._set_rate(rate)
        await self._notify_waiters()

    async def _notify_waiters(self) -> None:
        # Wakes waiters on this event loop. Waiters on other threads' loops pick up
        # the new rate when their current wait times out.
        condition = self._get_condition()
        async with condition:
            condition.notify_all()


class AsyncRequestRateTracker(_RequestRateTrackerBase):
    """AsyncRequestRateTracker tracks the client's request sending rate.

    AsyncRequestRateTracker measures the actual client request sending rate using
    time-bucketed sampling with exponential smoothing. It tracks requests in
    half-second intervals by default and calculates a smoothed average rate
    to provide accurate measurements for adaptive rate limiting algorithms.
    """

    async def measure_rate(self) -> float:
        """Measure and return the current request rate.

        Increments the request count and calculates a new smoothed rate when
        transitioning to a new time bucket. Returns the current measured rate
        without recalculation if still within the same time bucket.
        :return: Current smoothed request rate in requests per second.
        """
        return self._measure()


class AsyncClientRateLimiter(
    _ClientRateLimiterBase[AsyncTokenBucket, AsyncRequestRateTracker]
):
    """AsyncClientRateLimiter limits the rate of requests.

    AsyncClientRateLimiter implements adaptive rate limiting using token bucket and CUBIC
    algorithm. It controls request sending rates by acquiring tokens before requests
    and dynamically adjusting rates based on service responses - reducing rates when
    throttled and increasing rates during successful periods to optimize throughput
    while preventing service overload.
    """

    async def before_sending_request(self) -> None:
        """Acquire a token before making a request."""
        if self._rate_limiter_enabled:
            await self._token_bucket.acquire(self._REQUEST_COST)

    async def after_receiving_response(self, throttling_error: bool) -> None:
        """Update the request rate based on the response using CUBIC algorithm.

        Reduces the rate by 30% when throttled, or increases the rate using
        CUBIC scaling for successful responses. Updates the token bucket with
        the new calculated rate, capped at 2x the measured client rate.
        :param throttling_error: True if the response was a throttling error.
        """
        measured_rate = await self._rate_tracker.measure_rate()
        self._update_rate(measured_rate, throttling_error)
        await self._token_bucket._notify_waiters()  # pyright: ignore[reportPrivateUsage]


class AsyncAdaptiveRetryStrategy(
    _AdaptiveRetryStrategyBase, AsyncStandardRetryStrategy
):
    """Adaptive retry strategy with client-side rate limiting using CUBIC algorithm.

    Builds on top of AsyncStandardRetryStrategy by adding token bucket rate limiting and
    CUBIC congestion control. Rate limiting is enabled after the first throttling
    response and dynamically adjusts sending rates based on the response type.

    Use this strategy when a client sends a high volume of requests to a service and
    frequently receives throttling errors. Rather than only backing off individual
    retries, it slows the client's overall sending rate, reducing requests that are
    throttled and wasted on retries.
    """

    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        throttling_backoff_strategy: retries_interface.RetryBackoffStrategy
        | None = None,
        max_attempts: int = 3,
        retry_quota: StandardRetryQuota | None = None,
        rate_limiter: AsyncClientRateLimiter | None = None,
    ):
        """Initialize AsyncAdaptiveRetryStrategy.

        :param backoff_strategy: The backoff strategy used to compute the retry delay
            for non-throttling errors. Defaults to a 50ms-base
            :py:class:`ExponentialRetryBackoffStrategy`.

        :param throttling_backoff_strategy: The backoff strategy used to compute the
            retry delay for throttling errors. Defaults to a 1000ms-base
            :py:class:`ExponentialRetryBackoffStrategy`.

        :param max_attempts: Upper limit on total number of attempts made, including
            initial attempt and retries.

        :param retry_quota: The retry quota to use for managing retry capacity. Defaults
            to a new :py:class:`StandardRetryQuota` instance.

        :param rate_limiter: Optional pre-configured rate limiter. If None, creates
            default components with rate limiting initially disabled.
        """
        super().__init__(
            backoff_strategy=backoff_strategy,
            throttling_backoff_strategy=throttling_backoff_strategy,
            max_attempts=max_attempts,
            retry_quota=retry_quota,
        )
        self._rate_limiter = rate_limiter or AsyncClientRateLimiter(
            token_bucket=AsyncTokenBucket(),
            cubic_calculator=self._new_cubic_calculator(),
            rate_tracker=AsyncRequestRateTracker(),
            rate_limiter_enabled=False,  # Disabled until first throttle
        )

    @property
    def rate_limiter(self) -> AsyncClientRateLimiter:
        """Get the rate limiter for integration with request pipeline."""
        return self._rate_limiter

    async def acquire_from_token_bucket(self) -> None:
        if self._rate_limiter.rate_limit_enabled:
            await self._rate_limiter.before_sending_request()


class AsyncRetryStrategyResolver(_RetryStrategyResolverBase[AsyncRetryStrategy]):
    """Retry strategy resolver that caches retry strategies based on configuration options.

    This resolver caches retry strategy instances based on their configuration to reuse existing
    instances of AsyncRetryStrategy with the same settings. Each resolver has its own cache, so a
    client keeps its strategies, and any state they hold such as an adaptive rate limiter,
    for as long as the client exists, no matter how many other clients are created.
    """

    _STRATEGY_TYPES: ClassVar[dict[RetryStrategyType, Any]] = {
        "simple": AsyncSimpleRetryStrategy,
        "standard": AsyncStandardRetryStrategy,
        "adaptive": AsyncAdaptiveRetryStrategy,
    }

    async def resolve_retry_strategy(
        self,
        *,
        retry_strategy: AsyncRetryStrategy | RetryStrategyOptions | None,
        retry_mode: RetryStrategyType | None = None,
        max_attempts: int | None = None,
    ) -> AsyncRetryStrategy:
        """Resolve a retry strategy from the provided options, using cache when possible.

        :param retry_strategy: An explicitly configured retry strategy or options for
            creating one. Takes precedence over ``retry_mode``/``max_attempts``.
        :param retry_mode: Retry mode to fall back on when ``retry_strategy`` is None,
            typically resolved from the ``AWS_RETRY_MODE`` env var or a config profile.
        :param max_attempts: Maximum attempts to fall back on when ``retry_strategy`` is
            None, typically resolved from ``AWS_MAX_ATTEMPTS`` or a config profile.
        """
        return self._resolve(
            retry_strategy=retry_strategy,
            retry_mode=retry_mode,
            max_attempts=max_attempts,
            strategy_protocol=AsyncRetryStrategy,
        )
