#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import math
import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from .exceptions import RetryError
from .interfaces import retries as retries_interface
from .interfaces.retries import RetryStrategy

RetryStrategyType = Literal["simple", "standard"]


@dataclass(kw_only=True, frozen=True)
class RetryStrategyOptions:
    """Options for configuring retry behavior."""

    retry_mode: RetryStrategyType = "standard"
    """The retry mode to use."""

    max_attempts: int | None = None
    """Maximum number of attempts (initial attempt plus retries). If None, uses the strategy's default."""


class RetryStrategyResolver:
    """Retry strategy resolver that caches retry strategies based on configuration options.

    This resolver caches retry strategy instances based on their configuration to reuse existing
    instances of RetryStrategy with the same settings. Uses LRU cache for thread-safe caching.
    """

    async def resolve_retry_strategy(
        self, *, retry_strategy: RetryStrategy | RetryStrategyOptions | None
    ) -> RetryStrategy:
        """Resolve a retry strategy from the provided options, using cache when possible.

        :param retry_strategy: An explicitly configured retry strategy or options for creating one.
        """
        if isinstance(retry_strategy, RetryStrategy):
            return retry_strategy
        elif retry_strategy is None:
            retry_strategy = RetryStrategyOptions()
        elif not isinstance(retry_strategy, RetryStrategyOptions):  # type: ignore[reportUnnecessaryIsInstance]
            raise TypeError(
                f"retry_strategy must be RetryStrategy, RetryStrategyOptions, or None, "
                f"got {type(retry_strategy).__name__}"
            )
        return self._create_retry_strategy(
            retry_strategy.retry_mode, retry_strategy.max_attempts
        )

    @lru_cache
    def _create_retry_strategy(
        self, retry_mode: RetryStrategyType, max_attempts: int | None
    ) -> RetryStrategy:
        kwargs = {"max_attempts": max_attempts}
        filtered_kwargs: dict[str, Any] = {
            k: v for k, v in kwargs.items() if v is not None
        }
        match retry_mode:
            case "simple":
                return SimpleRetryStrategy(**filtered_kwargs)
            case "standard":
                return StandardRetryStrategy(**filtered_kwargs)
            case _:
                raise ValueError(f"Unknown retry mode: {retry_mode}")


class ExponentialBackoffJitterType(Enum):
    """Jitter mode for exponential backoff.

    For use with :py:class:`ExponentialRetryBackoffStrategy`.
    """

    DEFAULT = 1
    """Truncated binary exponential backoff delay with equal jitter:

    .. code-block:: python

        capped = min(max_backoff, backoff_scale_value * 2 ** (retry_attempt - 1))
        (capped / 2) + random_between(0, capped / 2)

    Also known as "Equal Jitter". Similar to :py:var:`FULL` but always keep some of the
    backoff and jitters by a smaller amount.
    """

    NONE = 2
    """Truncated binary exponential backoff delay without jitter:

    .. code-block:: python

        min(max_backoff, backoff_scale_value * 2 ** (retry_attempt - 1))
    """

    FULL = 3
    """Truncated binary exponential backoff delay with full jitter:

    .. code-block:: python

        random_between(
            max_backoff,
            min(max_backoff, backoff_scale_value * 2 ** (retry_attempt - 1))
        )
    """

    DECORRELATED = 4
    """Truncated binary exponential backoff delay with decorrelated jitter:

    .. code-block:: python

        min(max_backoff, random_between(backoff_scale_value, t_(i-1) * 3))

    Similar to :py:var:`FULL`, but also increases the maximum jitter at each retry.
    """


class ExponentialRetryBackoffStrategy(retries_interface.RetryBackoffStrategy):
    def __init__(
        self,
        *,
        backoff_scale_value: float = 0.025,
        max_backoff: float = 20,
        jitter_type: ExponentialBackoffJitterType = ExponentialBackoffJitterType.DEFAULT,
        random: Callable[[], float] = random.random,
    ):
        """Exponential backoff with optional jitter.

        .. seealso:: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

        :param backoff_scale_value: Factor that linearly adjusts returned backoff delay
        values. See the methods ``_next_delay_*`` for the formula used to calculate the
        delay for each jitter type. If set to ``None`` (the default), :py:attr:`random`
        will be called to generate a value.

        :param max_backoff: Upper limit for backoff delay values returned, in seconds.

        :param jitter_type: Determines the formula used to apply jitter to the backoff
        delay.

        :param random: A callable that returns random numbers between ``0`` and ``1``.
        Use the default ``random.random`` unless you require an alternate source of
        randomness or a non-uniform distribution.
        """
        self._backoff_scale_value = backoff_scale_value
        self._max_backoff = max_backoff
        self._jitter_type = jitter_type
        self._random = random
        self._previous_delay_seconds = self._backoff_scale_value

    def compute_next_backoff_delay(self, retry_attempt: int) -> float:
        """Calculate timespan in seconds to delay before next retry.

        See the methods ``_next_delay_*`` for the formula used to calculate the delay
        for each jitter type for values of ``retry_attempt > 0``.

        :param retry_attempt: The index of the retry attempt that is about to be made
        after the delay. The initial attempt, before any retries, is index ``0``, and
        will return a delay of ``0``. The first retry attempt after a failed initial
        attempt is index ``1``, and so on.
        """
        if retry_attempt == 0:
            return 0

        match self._jitter_type:
            case ExponentialBackoffJitterType.NONE:
                seconds = self._next_delay_no_jitter(retry_attempt=retry_attempt)
            case ExponentialBackoffJitterType.DEFAULT:
                seconds = self._next_delay_equal_jitter(retry_attempt=retry_attempt)
            case ExponentialBackoffJitterType.FULL:
                seconds = self._next_delay_full_jitter(retry_attempt=retry_attempt)
            case ExponentialBackoffJitterType.DECORRELATED:
                seconds = self._next_delay_decorrelated_jitter(
                    previous_delay=self._previous_delay_seconds
                )

        self._previous_delay_seconds = seconds
        return seconds

    def _jitter_free_uncapped_delay(self, retry_attempt: int) -> float:
        """The basic exponential delay without jitter or upper bound:

        .. code-block:: python

            backoff_scale_value * 2 ** (retry_attempt - 1)
        """
        return self._backoff_scale_value * (2.0 ** (retry_attempt - 1))

    def _next_delay_no_jitter(self, retry_attempt: int) -> float:
        """Calculates truncated binary exponential backoff delay without jitter.

        Used when :py:var:`jitter_type` is :py:attr:`ExponentialBackoffJitterType.NONE`.
        """
        no_jitter_delay = self._jitter_free_uncapped_delay(retry_attempt)
        return min(no_jitter_delay, self._max_backoff)

    def _next_delay_full_jitter(self, retry_attempt: int) -> float:
        """Calculates truncated binary exponential backoff delay with full jitter.

        Used when :py:var:`jitter_type` is :py:attr:`ExponentialBackoffJitterType.FULL`.
        """

        no_jitter_delay = self._jitter_free_uncapped_delay(retry_attempt)
        return self._random() * min(no_jitter_delay, self._max_backoff)

    def _next_delay_equal_jitter(self, retry_attempt: int) -> float:
        """Calculates truncated binary exponential backoff delay with equal jitter:

        Used when :py:var:`jitter_type` is
        :py:attr:`ExponentialBackoffJitterType.DEFAULT`.
        """
        no_jitter_delay = self._jitter_free_uncapped_delay(retry_attempt)
        return (self._random() * 0.5 + 0.5) * min(no_jitter_delay, self._max_backoff)

    def _next_delay_decorrelated_jitter(self, previous_delay: float) -> float:
        """Calculates truncated binary exp. backoff delay with decorrelated jitter:

        Used when :py:var:`jitter_type` is
        :py:attr:`ExponentialBackoffJitterType.DECORRELATED`.
        """
        return min(
            self._backoff_scale_value + self._random() * previous_delay * 3,
            self._max_backoff,
        )


@dataclass(kw_only=True)
class SimpleRetryToken:
    """Basic retry token that stores only the attempt count and backoff strategy.

    Retry tokens should always be obtained from an implementation of
    :py:class:`retries_interface.RetryStrategy`.
    """

    retry_count: int
    """Retry count is the total number of attempts minus the initial attempt."""

    retry_delay: float
    """Delay in seconds to wait before the retry attempt."""

    @property
    def attempt_count(self) -> int:
        """The total number of attempts including the initial attempt and retries."""
        return self.retry_count + 1


class SimpleRetryStrategy(retries_interface.RetryStrategy):
    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        max_attempts: int = 5,
    ):
        """Basic retry strategy that simply invokes the given backoff strategy.

        :param backoff_strategy: The backoff strategy used by returned tokens to compute
        the retry delay. Defaults to :py:class:`ExponentialRetryBackoffStrategy`.

        :param max_attempts: Upper limit on total number of attempts made, including
        initial attempt and retries.
        """
        self.backoff_strategy = backoff_strategy or ExponentialRetryBackoffStrategy()
        self.max_attempts = max_attempts

    def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> SimpleRetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: This argument is ignored by this retry strategy.
        """
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return SimpleRetryToken(retry_count=0, retry_delay=retry_delay)

    def refresh_retry_token_for_retry(
        self,
        *,
        token_to_renew: retries_interface.RetryToken,
        error: Exception,
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

    def record_success(self, *, token: retries_interface.RetryToken) -> None:
        """Not used by this retry strategy."""

    def __deepcopy__(self, memo: Any) -> "SimpleRetryStrategy":
        return self


class StandardRetryQuota:
    """Retry quota used by :py:class:`StandardRetryStrategy`."""

    INITIAL_RETRY_TOKENS: int = 500
    RETRY_COST: int = 5
    NO_RETRY_INCREMENT: int = 1
    TIMEOUT_RETRY_COST: int = 10

    def __init__(self, initial_capacity: int = INITIAL_RETRY_TOKENS):
        """Initialize retry quota with configurable capacity.

        :param initial_capacity: The initial and maximum capacity for the retry quota.
        """
        self._max_capacity = initial_capacity
        self._available_capacity = initial_capacity
        self._lock = threading.Lock()

    def acquire(self, *, error: Exception) -> int:
        """Attempt to acquire capacity for a retry attempt.

        If there's insufficient capacity available, raise an exception.
        Otherwise, return the amount of capacity successfully allocated.
        """

        is_timeout = (
            isinstance(error, retries_interface.ErrorRetryInfo)
            and error.is_timeout_error
        )
        capacity_amount = self.TIMEOUT_RETRY_COST if is_timeout else self.RETRY_COST

        with self._lock:
            if capacity_amount > self._available_capacity:
                raise RetryError("Retry quota exceeded")
            self._available_capacity -= capacity_amount
            return capacity_amount

    def release(self, *, release_amount: int) -> None:
        """Release capacity back to the retry quota.

        The capacity being released will be truncated if necessary to ensure the max
        capacity is never exceeded.
        """
        increment = self.NO_RETRY_INCREMENT if release_amount == 0 else release_amount

        if self._available_capacity == self._max_capacity:
            return

        with self._lock:
            self._available_capacity = min(
                self._available_capacity + increment, self._max_capacity
            )

    @property
    def available_capacity(self) -> int:
        """Return the amount of capacity available."""
        return self._available_capacity


@dataclass(kw_only=True)
class StandardRetryToken:
    retry_count: int
    """Retry count is the total number of attempts minus the initial attempt."""

    retry_delay: float
    """Delay in seconds to wait before the retry attempt."""

    quota_acquired: int = 0
    """The amount of quota acquired for this retry attempt."""


class StandardRetryStrategy(retries_interface.RetryStrategy):
    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        max_attempts: int = 3,
        retry_quota: StandardRetryQuota | None = None,
    ):
        """Standard retry strategy using truncated binary exponential backoff with full
        jitter.

        :param backoff_strategy: The backoff strategy used by returned tokens to compute
        the retry delay. Defaults to :py:class:`ExponentialRetryBackoffStrategy`.

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
            backoff_scale_value=1,
            max_backoff=20,
            jitter_type=ExponentialBackoffJitterType.FULL,
        )
        self.max_attempts = max_attempts
        self._retry_quota = retry_quota or StandardRetryQuota()

    def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> StandardRetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: This argument is ignored by this retry strategy.
        """
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return StandardRetryToken(retry_count=0, retry_delay=retry_delay)

    def refresh_retry_token_for_retry(
        self,
        *,
        token_to_renew: retries_interface.RetryToken,
        error: Exception,
    ) -> StandardRetryToken:
        """Replace an existing retry token from a failed attempt with a new token.

        This retry strategy always returns a token until the attempt count stored in
        the new token exceeds the ``max_attempts`` value.

        :param token_to_renew: The token used for the previous failed attempt.
        :param error: The error that triggered the need for a retry.
        :raises RetryError: If no further retry attempts are allowed.
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

            # Acquire additional quota for this retry attempt
            # (may raise a RetryError if none is available)
            quota_acquired = self._retry_quota.acquire(error=error)

            if error.retry_after is not None:
                retry_delay = error.retry_after
            else:
                retry_delay = self.backoff_strategy.compute_next_backoff_delay(
                    retry_count
                )

            return StandardRetryToken(
                retry_count=retry_count,
                retry_delay=retry_delay,
                quota_acquired=quota_acquired,
            )
        else:
            raise RetryError(f"Error is not retryable: {error}") from error

    def record_success(self, *, token: retries_interface.RetryToken) -> None:
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
    """

    MIN_FILL_RATE = 0.5  # Minimum allowed fill rate (0.5 tokens/second)
    MIN_CAPACITY = 1.0  # Minimum allowed bucket capacity (1.0 tokens)
    DEFAULT_TIMEOUT = 30.0  # Default timeout for token acquisition (30.0 seconds)

    def __init__(
        self,
        *,
        curr_capacity: float = MIN_CAPACITY,
        fill_rate: float = MIN_FILL_RATE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize a new TokenBucket.

        :param curr_capacity: Initial number of tokens in the bucket.
        :param fill_rate: Rate at which tokens are added to the bucket (tokens/second).
        :param timeout: Maximum time to wait for token acquisition before
        raising TimeoutError.
        """
        self._curr_capacity: float = max(curr_capacity, self.MIN_CAPACITY)
        self._max_capacity: float = self._curr_capacity
        self._fill_rate: float = max(fill_rate, self.MIN_FILL_RATE)
        self._timeout = timeout
        self._last_timestamp: float = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, amount: float) -> None:
        """Acquire tokens from the bucket.

        If sufficient tokens are available, they are immediately consumed and the
        method returns. If insufficient tokens are available, the method will wait
        until enough tokens have been refilled or the timeout is reached.

        :param amount: Number of tokens to acquire.

        :raises TimeoutError: Acquisition took longer than the configured timeout.
        """
        start_time = time.monotonic()
        while True:
            async with self._lock:
                self._refill()
                if self._curr_capacity >= amount:
                    self._curr_capacity -= amount
                    return

                elapsed = time.monotonic() - start_time
                if elapsed > self._timeout:
                    # This will be caught in retry strategy and used as part of the retry count
                    raise TimeoutError(
                        f"Failed to acquire {amount} tokens within {self._timeout}s"
                    )
                wait_time = (amount - self._curr_capacity) / self._fill_rate
            await asyncio.sleep(wait_time)

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
        async with self._lock:
            self._refill()
            self._fill_rate = max(rate, self.MIN_FILL_RATE)
            self._max_capacity = max(rate, self.MIN_CAPACITY)
            self._curr_capacity = min(self._curr_capacity, self._max_capacity)

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


class CubicCalculator:
    """CubicCalculator calculates a new rate using a modified CUBIC algorithm.

    CubicCalculator implements the CUBIC congestion control algorithm for
    adaptive rate limiting. It dynamically adjusts request rates based on
    throttling responses, reducing rates by 30% when throttled and
    gradually increasing rates using a scale function when the request
    is successful.
    """

    # Scale constant used to scale up requests
    _SCALE_CONSTANT = 0.4
    # Beta constant used to slow down requests
    _BETA = 0.7

    def __init__(
        self,
        starting_max_rate: float = 0.5,
        start_time: float | None = None,
    ):
        """Initialize a new CubicCalculator.

        :param starting_max_rate: Initial maximum request per second.
        :param start_time: Initial time of the CubicCalculator.
        """
        if starting_max_rate <= 0:
            raise ValueError(
                f"starting_max_rate must be positive, got {starting_max_rate}"
            )
        if start_time is None:
            start_time = time.monotonic()

        self._last_max_rate = starting_max_rate
        self._last_throttle_time = start_time
        self._inflection_point_time = self.calculate_and_update_inflection_point()

    def calculate_and_update_inflection_point(self) -> float:
        """Calculate and update the CUBIC inflection point for rate recovery.

        After throttling, the CUBIC curve returns to the previous maximum rate
        after exactly `_inflection_point_time` seconds. Before this point, the
        rate grows slowly. After this point, it grows rapidly.
        :return: Inflection point time in seconds for the CUBIC algorithm.
        """
        self._inflection_point_time = (
            (self._last_max_rate * (1 - self._BETA)) / self._SCALE_CONSTANT
        ) ** (1 / 3.0)
        return self._inflection_point_time

    def calculate_scaled_request_rate(self, timestamp: float) -> float:
        """Scale up the request rate after a successful response.

        :param timestamp: Timestamp of the response.
        :return: New calculated request rate based on CUBIC scaling.
        """
        dt = timestamp - self._last_throttle_time
        calculated_rate = (
            self._SCALE_CONSTANT * ((dt - self._inflection_point_time) ** 3)
        ) + self._last_max_rate
        return calculated_rate

    def calculate_throttled_request_rate(
        self, rate_to_use: float, timestamp: float
    ) -> float:
        """Throttle the request rate after a throttled response is received.

        :param rate_to_use: Current request rate in use.
        :param timestamp: Timestamp of the response.
        :return: New calculated request rate based on CUBIC throttling.
        """
        calculated_rate = rate_to_use * self._BETA
        self._last_max_rate = rate_to_use
        self._last_throttle_time = timestamp
        return calculated_rate

    @property
    def last_max_rate(self) -> float:
        return self._last_max_rate

    @property
    def last_throttle_time(self) -> float:
        return self._last_throttle_time


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
        self._lock = asyncio.Lock()

    async def measure_rate(self) -> float:
        """Measure and return the current request rate.

        Increments the request count and calculates a new smoothed rate when
        transitioning to a new time bucket. Returns the current measured rate
        without recalculation if still within the same time bucket.
        :return: Current smoothed request rate in requests per second.
        """
        async with self._lock:
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
        timestamp = time.monotonic()
        if throttling_error:
            if not self._rate_limiter_enabled:
                rate_to_use = measured_rate
            else:
                fill_rate = self._token_bucket.fill_rate
                rate_to_use = min(measured_rate, fill_rate)

            self._cubic_calculator.calculate_and_update_inflection_point()
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
        await self._token_bucket.update_rate(new_rate)

    @property
    def rate_limit_enabled(self) -> bool:
        return self._rate_limiter_enabled
