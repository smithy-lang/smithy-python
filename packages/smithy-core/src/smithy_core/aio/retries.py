#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import math
import threading
import time
import weakref
from typing import Any

from ..exceptions import RetryError
from ..interfaces import retries as retries_interface
from ..retries import (
    CubicCalculator,
    ExponentialBackoffJitterType,
    ExponentialRetryBackoffStrategy,
    RetryStrategyOptions,
    RetryStrategyType,
    SimpleRetryToken,
    StandardRetryQuota,
    StandardRetryToken,
)
from .interfaces.retries import RetryStrategy

__all__ = [
    "AdaptiveRetryStrategy",
    "ClientRateLimiter",
    "RequestRateTracker",
    "RetryStrategyResolver",
    "SimpleRetryStrategy",
    "StandardRetryStrategy",
    "TokenBucket",
]


class RetryStrategyResolver:
    """Retry strategy resolver that caches retry strategies based on configuration options.

    This resolver caches retry strategy instances based on their configuration to reuse existing
    instances of RetryStrategy with the same settings. Each resolver has its own cache, so a
    client keeps its strategies, and any state they hold such as an adaptive rate limiter,
    for as long as the client exists, no matter how many other clients are created.
    """

    def __init__(self) -> None:
        self._strategies: dict[tuple[RetryStrategyType, int | None], RetryStrategy] = {}

    async def resolve_retry_strategy(
        self,
        *,
        retry_strategy: RetryStrategy | RetryStrategyOptions | None,
        retry_mode: RetryStrategyType | None = None,
        max_attempts: int | None = None,
    ) -> RetryStrategy:
        """Resolve a retry strategy from the provided options, using cache when possible.

        :param retry_strategy: An explicitly configured retry strategy or options for
            creating one. Takes precedence over ``retry_mode``/``max_attempts``.
        :param retry_mode: Retry mode to fall back on when ``retry_strategy`` is None,
            typically resolved from the ``AWS_RETRY_MODE`` env var or a config profile.
        :param max_attempts: Maximum attempts to fall back on when ``retry_strategy`` is
            None, typically resolved from ``AWS_MAX_ATTEMPTS`` or a config profile.
        """
        if isinstance(retry_strategy, RetryStrategy):
            return retry_strategy
        elif retry_strategy is None:
            # Fall back to the separately-resolved config values.
            retry_strategy = RetryStrategyOptions(
                retry_mode=retry_mode if retry_mode is not None else "standard",
                max_attempts=max_attempts,
            )
        elif not isinstance(retry_strategy, RetryStrategyOptions):  # type: ignore[reportUnnecessaryIsInstance]
            raise TypeError(
                f"retry_strategy must be RetryStrategy, RetryStrategyOptions, or None, "
                f"got {type(retry_strategy).__name__}"
            )
        return self._create_retry_strategy(
            retry_strategy.retry_mode, retry_strategy.max_attempts
        )

    def _create_retry_strategy(
        self, retry_mode: RetryStrategyType, max_attempts: int | None
    ) -> RetryStrategy:
        key = (retry_mode, max_attempts)
        if key not in self._strategies:
            self._strategies[key] = self._new_retry_strategy(retry_mode, max_attempts)
        return self._strategies[key]

    def _new_retry_strategy(
        self, retry_mode: RetryStrategyType, max_attempts: int | None
    ) -> RetryStrategy:
        kwargs: dict[str, Any] = {"max_attempts": max_attempts}
        filtered_kwargs: dict[str, Any] = {
            k: v for k, v in kwargs.items() if v is not None
        }
        match retry_mode:
            case "simple":
                return SimpleRetryStrategy(**filtered_kwargs)
            case "standard":
                return StandardRetryStrategy(**filtered_kwargs)
            case "adaptive":
                return AdaptiveRetryStrategy(**filtered_kwargs)
            case _:
                raise ValueError(f"Unknown retry mode: {retry_mode}")


class SimpleRetryStrategy:
    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        max_attempts: int = 5,
    ):
        """Retry strategy that simply invokes the given backoff strategy.

        :param backoff_strategy: The backoff strategy used by returned tokens to compute
            the retry delay. Defaults to :py:class:`ExponentialRetryBackoffStrategy`.

        :param max_attempts: Upper limit on total number of attempts made, including
            initial attempt and retries.
        """
        self.backoff_strategy = backoff_strategy or ExponentialRetryBackoffStrategy()
        self.max_attempts = max_attempts

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> SimpleRetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: This argument is ignored by this retry strategy.
        """
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return SimpleRetryToken(retry_count=0, retry_delay=retry_delay)

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
        if isinstance(error, retries_interface.ErrorRetryInfo) and error.is_retry_safe:
            retry_count = token_to_renew.retry_count + 1
            if retry_count >= self.max_attempts:
                raise RetryError(
                    f"Reached maximum number of allowed attempts: {self.max_attempts}"
                ) from error
            retry_delay = self.backoff_strategy.compute_next_backoff_delay(retry_count)
            return SimpleRetryToken(retry_count=retry_count, retry_delay=retry_delay)
        else:
            raise RetryError(f"Error is not retryable: {error}") from error

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        """Not used by this retry strategy."""

    def __deepcopy__(self, memo: Any) -> "SimpleRetryStrategy":
        return self


class StandardRetryStrategy:
    _RETRY_AFTER_MAX_ADDITIONAL: float = 5
    """Upper bound (seconds) for additional delay beyond the computed backoff."""

    _NON_THROTTLING_BACKOFF_SCALE: float = 0.05
    """Base backoff scale (seconds) for non-throttling errors (50ms)."""

    _THROTTLING_BACKOFF_SCALE: float = 1
    """Base backoff scale (seconds) for throttling errors (1000ms)."""

    _MAX_BACKOFF: float = 20
    """Upper bound (seconds) for the computed backoff, applied before jitter."""

    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        throttling_backoff_strategy: retries_interface.RetryBackoffStrategy
        | None = None,
        max_attempts: int = 3,
        retry_quota: StandardRetryQuota | None = None,
    ):
        """Standard retry strategy using truncated binary exponential backoff
        with full jitter.

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
        """
        if max_attempts < 0:
            raise ValueError(
                f"max_attempts must be a non-negative integer, got {max_attempts}"
            )

        self.backoff_strategy = backoff_strategy or ExponentialRetryBackoffStrategy(
            backoff_scale_value=self._NON_THROTTLING_BACKOFF_SCALE,
            max_backoff=self._MAX_BACKOFF,
            jitter_type=ExponentialBackoffJitterType.FULL,
        )
        self.throttling_backoff_strategy = (
            throttling_backoff_strategy
            or ExponentialRetryBackoffStrategy(
                backoff_scale_value=self._THROTTLING_BACKOFF_SCALE,
                max_backoff=self._MAX_BACKOFF,
                jitter_type=ExponentialBackoffJitterType.FULL,
            )
        )
        self.max_attempts = max_attempts
        self._retry_quota = retry_quota or StandardRetryQuota()

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> StandardRetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: This argument is ignored by this retry strategy.
        """
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return StandardRetryToken(retry_count=0, retry_delay=retry_delay)

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
        if not isinstance(token_to_renew, StandardRetryToken):
            raise TypeError(
                f"StandardRetryStrategy requires StandardRetryToken, got {type(token_to_renew).__name__}"
            )

        if isinstance(error, retries_interface.ErrorRetryInfo) and error.is_retry_safe:
            retry_count = token_to_renew.retry_count + 1
            if retry_count >= self.max_attempts:
                raise RetryError(
                    f"Reached maximum number of allowed attempts: {self.max_attempts}"
                ) from error

            # Throttling errors use a larger base backoff than other errors.
            backoff_strategy = (
                self.throttling_backoff_strategy
                if error.is_throttling_error
                else self.backoff_strategy
            )
            t_i = backoff_strategy.compute_next_backoff_delay(retry_count)

            if error.retry_after is not None:
                # Bound a server-directed backoff to [t_i, t_i + 5] seconds.
                retry_delay = max(
                    t_i, min(error.retry_after, self._RETRY_AFTER_MAX_ADDITIONAL + t_i)
                )
            else:
                retry_delay = t_i

            try:
                quota_acquired = self._retry_quota.acquire(error=error)
            except RetryError as quota_error:
                # Surface the computed delay so callers can back off before giving
                # up; long-polling operations sleep for it before returning.
                raise RetryError(str(quota_error), retry_after=retry_delay) from error

            return StandardRetryToken(
                retry_count=retry_count,
                retry_delay=retry_delay,
                quota_acquired=quota_acquired,
            )
        else:
            raise RetryError(f"Error is not retryable: {error}") from error

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        """Release retry quota back based on the amount consumed by the last retry.

        :param token: The token used for the previous successful attempt.
        """
        if not isinstance(token, StandardRetryToken):
            raise TypeError(
                f"StandardRetryStrategy requires StandardRetryToken, got {type(token).__name__}"
            )
        self._retry_quota.release(release_amount=token.quota_acquired)

    def __deepcopy__(self, memo: Any) -> "StandardRetryStrategy":
        return self


class TokenBucket:
    """Token bucket for rate limiting with configurable fill rate.

    TokenBucket provides a collection of arbitrary tokens while managing issuance
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

    MIN_FILL_RATE = 0.5  # Minimum allowed fill rate (0.5 tokens/second)
    MIN_CAPACITY = 1.0  # Minimum allowed bucket capacity (1.0 tokens)
    DEFAULT_TIMEOUT = 30.0  # Default timeout for token acquisition (30.0 seconds)

    def __init__(
        self,
        *,
        curr_capacity: float = 0,
        fill_rate: float = MIN_FILL_RATE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize a new TokenBucket.

        :param curr_capacity: Initial number of tokens in the bucket. The bucket can
            hold at least MIN_CAPACITY tokens, but starts empty by default.
        :param fill_rate: Rate at which tokens are added to the bucket (tokens/second).
        :param timeout: Maximum time to wait for token acquisition before
        raising TimeoutError.
        """
        self._curr_capacity: float = curr_capacity
        self._max_capacity: float = max(curr_capacity, self.MIN_CAPACITY)
        self._fill_rate: float = max(fill_rate, self.MIN_FILL_RATE)
        self._timeout = timeout
        self._last_timestamp: float = time.monotonic()
        self._lock = threading.Lock()
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
        start_time = time.monotonic()
        condition = self._get_condition()
        async with condition:
            while True:
                with self._lock:
                    self._refill()
                    if self._curr_capacity >= amount:
                        self._curr_capacity -= amount
                        return
                    wait_time = (amount - self._curr_capacity) / self._fill_rate

                elapsed = time.monotonic() - start_time
                if elapsed >= self._timeout:
                    # Fails the request; this is not counted as a retry attempt
                    raise TimeoutError(
                        f"Failed to acquire {amount} tokens within {self._timeout}s"
                    )
                # Wait outside the thread lock, and never past the timeout
                try:
                    await asyncio.wait_for(
                        condition.wait(),
                        timeout=min(wait_time, self._timeout - elapsed),
                    )
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

    def _refill(self) -> None:
        curr_time = time.monotonic()
        elapsed = curr_time - self._last_timestamp
        refill_amount = elapsed * self._fill_rate
        self._curr_capacity = min(
            self._max_capacity, self._curr_capacity + refill_amount
        )
        self._last_timestamp = curr_time

    async def update_rate(self, rate: float) -> None:
        """Update the bucket's fill rate, maximum capacity and current capacity (if its
        greater than maximum capacity).

        :param rate: New fill rate (tokens/second). It won't be less than MIN_FILL_RATE.
            Current capacity will be reduced if it exceeds the new maximum capacity.
        """
        self._set_rate(rate)
        await self._notify_waiters()

    def _set_rate(self, rate: float) -> None:
        with self._lock:
            self._refill()
            self._fill_rate = max(rate, self.MIN_FILL_RATE)
            self._max_capacity = max(rate, self.MIN_CAPACITY)
            self._curr_capacity = min(self._curr_capacity, self._max_capacity)

    async def _notify_waiters(self) -> None:
        # Wakes waiters on this event loop. Waiters on other threads' loops pick up
        # the new rate when their current wait times out.
        condition = self._get_condition()
        async with condition:
            condition.notify_all()

    @property
    def current_capacity(self) -> float:
        """Get the current number of tokens in the bucket.

        :return: The current token count as of the last refill operation.
        """
        return self._curr_capacity

    @property
    def max_capacity(self) -> float:
        """Get the maximum capacity of the bucket.

        :return: The maximum number of tokens the bucket can hold.
        """
        return self._max_capacity

    @property
    def fill_rate(self) -> float:
        """Get the current fill rate of the bucket.

        :return: The rate at which tokens are added to the bucket (tokens/second).
        """
        return self._fill_rate


class RequestRateTracker:
    """RequestRateTracker tracks the client's request sending rate.

    RequestRateTracker measures the actual client request sending rate using
    time-bucketed sampling with exponential smoothing. It tracks requests in
    half-second intervals by default and calculates a smoothed average rate
    to provide accurate measurements for adaptive rate limiting algorithms.
    """

    _DEFAULT_SMOOTHING = 0.8
    _TIME_BUCKET_RANGE = 0.5

    def __init__(
        self,
        smoothing: float = _DEFAULT_SMOOTHING,
        time_bucket_range: float = _TIME_BUCKET_RANGE,
    ):
        """Initialize a new RequestRateTracker.

        :param smoothing: Exponential smoothing factor. This constant
        represents how much weight is given to recent measurements.
        Higher values place more emphasis on the most recent observations.
        :param time_bucket_range: Time bucket duration in seconds. Rate
        calculations are updated when transitioning between buckets.
        """
        self._smoothing = smoothing
        self._time_bucket_scale = 1 / time_bucket_range
        self._request_count = 0
        self._last_calculated_time_bucket = math.floor(time.monotonic())
        self._measured_rate = 0
        # The update never awaits, so it only needs protecting across threads
        self._lock = threading.Lock()

    async def measure_rate(self) -> float:
        """Measure and return the current request rate.

        Increments the request count and calculates a new smoothed rate when
        transitioning to a new time bucket. Returns the current measured rate
        without recalculation if still within the same time bucket.
        :return: Current smoothed request rate in requests per second.
        """
        with self._lock:
            curr_time = time.monotonic()
            current_time_bucket = (
                math.floor(curr_time * self._time_bucket_scale)
                / self._time_bucket_scale
            )
            self._request_count += 1
            if current_time_bucket > self._last_calculated_time_bucket:
                current_rate = self._request_count / (
                    current_time_bucket - self._last_calculated_time_bucket
                )
                self._measured_rate = (current_rate * self._smoothing) + (
                    self._measured_rate * (1 - self._smoothing)
                )
                self._request_count = 0
                self._last_calculated_time_bucket = current_time_bucket
            return self._measured_rate

    @property
    def request_count(self) -> int:
        """Get current request count. For testing only."""
        return self._request_count

    @property
    def measured_client_rate(self) -> float:
        """Get the client's sending rate. For testing only."""
        return self._measured_rate


class ClientRateLimiter:
    """ClientRateLimiter limits the rate of requests.

    ClientRateLimiter implements adaptive rate limiting using token bucket and CUBIC
    algorithm. It controls request sending rates by acquiring tokens before requests
    and dynamically adjusting rates based on service responses - reducing rates when
    throttled and increasing rates during successful periods to optimize throughput
    while preventing service overload.
    """

    _REQUEST_COST = 1.0

    def __init__(
        self,
        token_bucket: TokenBucket,
        cubic_calculator: CubicCalculator,
        rate_tracker: RequestRateTracker,
        rate_limiter_enabled: bool,
    ):
        """Initialize a new ClientRateLimiter.

        :param token_bucket: Token bucket for controlling request sending rates.
        :param cubic_calculator: CUBIC algorithm calculator for rate adjustments.
        :param rate_tracker: Tracker for measuring actual client request rates.
        :param rate_limiter_enabled: Whether rate limiting is enabled.
        """

        self._rate_tracker = rate_tracker
        self._token_bucket = token_bucket
        self._cubic_calculator = cubic_calculator
        self._rate_limiter_enabled = rate_limiter_enabled
        self._lock = threading.Lock()

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
        with self._lock:
            timestamp = time.monotonic()
            if throttling_error:
                if not self._rate_limiter_enabled:
                    rate_to_use = measured_rate
                else:
                    fill_rate = self._token_bucket.fill_rate
                    rate_to_use = min(measured_rate, fill_rate)

                cubic_calculated_rate = (
                    self._cubic_calculator.calculate_throttled_request_rate(
                        rate_to_use, timestamp
                    )
                )
                self._rate_limiter_enabled = True
            else:
                cubic_calculated_rate = (
                    self._cubic_calculator.calculate_scaled_request_rate(timestamp)
                )

            new_rate = min(cubic_calculated_rate, 2 * measured_rate)
            # Set under the lock so rates reach the bucket in the order they're
            # calculated. Waking waiters awaits, so it happens after the lock.
            self._token_bucket._set_rate(new_rate)  # pyright: ignore[reportPrivateUsage]
        await self._token_bucket._notify_waiters()  # pyright: ignore[reportPrivateUsage]

    @property
    def rate_limit_enabled(self) -> bool:
        return self._rate_limiter_enabled


class AdaptiveRetryStrategy(StandardRetryStrategy):
    """Adaptive retry strategy with client-side rate limiting using CUBIC algorithm.

    Builds on top of StandardRetryStrategy by adding token bucket rate limiting and
    CUBIC congestion control. Rate limiting is enabled after the first throttling
    response and dynamically adjusts sending rates based on the response type.

    Use this strategy when a client sends a high volume of requests to a service and
    frequently receives throttling errors. Rather than only backing off individual
    retries, it slows the client's overall sending rate, reducing requests that are
    throttled and wasted on retries.
    """

    STARTING_MAX_RATE = 0

    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        throttling_backoff_strategy: retries_interface.RetryBackoffStrategy
        | None = None,
        max_attempts: int = 3,
        retry_quota: StandardRetryQuota | None = None,
        rate_limiter: ClientRateLimiter | None = None,
    ):
        """Initialize AdaptiveRetryStrategy.

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

        if rate_limiter is None:
            token_bucket = TokenBucket()
            cubic_calculator = CubicCalculator(
                starting_max_rate=self.STARTING_MAX_RATE, start_time=time.monotonic()
            )
            rate_tracker = RequestRateTracker()
            self._rate_limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=cubic_calculator,
                rate_tracker=rate_tracker,
                rate_limiter_enabled=False,  # Disabled until first throttle
            )
        else:
            self._rate_limiter = rate_limiter

    @property
    def rate_limiter(self) -> ClientRateLimiter:
        """Get the rate limiter for integration with request pipeline."""
        return self._rate_limiter

    def is_throttling_error(self, error: Exception) -> bool:
        """Check if error is a throttling error using existing ErrorRetryInfo."""
        if isinstance(error, retries_interface.ErrorRetryInfo):
            return error.is_throttling_error
        return False

    async def acquire_from_token_bucket(self) -> None:
        if self._rate_limiter.rate_limit_enabled:
            await self._rate_limiter.before_sending_request()

    def __deepcopy__(self, memo: Any) -> "AdaptiveRetryStrategy":
        return self
