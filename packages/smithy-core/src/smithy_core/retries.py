#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .exceptions import RetryError
from .interfaces import retries as retries_interface


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

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> SimpleRetryToken:
        """Called before any retries (for the first attempt at the operation).

        :param token_scope: This argument is ignored by this retry strategy.
        """
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return SimpleRetryToken(retry_count=0, retry_delay=retry_delay)

    async def refresh_retry_token_for_retry(
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

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        """Not used by this retry strategy."""


@dataclass(kw_only=True)
class StandardRetryToken:
    retry_count: int
    """Retry count is the total number of attempts minus the initial attempt."""

    retry_delay: float
    """Delay in seconds to wait before the retry attempt."""

    quota_consumed: int = 0
    """The total amount of quota consumed."""

    last_quota_acquired: int = 0
    """The amount of last quota acquired."""


class StandardRetryStrategy(retries_interface.RetryStrategy):
    def __init__(self, *, max_attempts: int = 3):
        """Standard retry strategy using truncated binary exponential backoff with full
        jitter.

        :param max_attempts: Upper limit on total number of attempts made, including
            initial attempt and retries.
        """
        self.backoff_strategy = ExponentialRetryBackoffStrategy(
            backoff_scale_value=1,
            jitter_type=ExponentialBackoffJitterType.FULL,
        )
        self.max_attempts = max_attempts
        self._retry_quota = StandardRetryQuota()

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> StandardRetryToken:
        """Called before any retries (for the first attempt at the operation).

        :param token_scope: This argument is ignored by this retry strategy.
        """
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return StandardRetryToken(retry_count=0, retry_delay=retry_delay)

    async def refresh_retry_token_for_retry(
        self,
        *,
        token_to_renew: StandardRetryToken,
        error: Exception,
    ) -> StandardRetryToken:
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

            # Acquire additional quota for this retry attempt
            # (may raise a RetryError if none is available)
            quota_acquired = await self._retry_quota.acquire(error=error)
            total_quota = token_to_renew.quota_consumed + quota_acquired

            if error.retry_after is not None:
                retry_delay = error.retry_after
            else:
                retry_delay = self.backoff_strategy.compute_next_backoff_delay(
                    retry_count
                )

            return StandardRetryToken(
                retry_count=retry_count,
                retry_delay=retry_delay,
                quota_consumed=total_quota,
                last_quota_acquired=quota_acquired,
            )
        else:
            raise RetryError(f"Error is not retryable: {error}") from error

    async def record_success(self, *, token: StandardRetryToken) -> None:
        """Return token after successful completion of an operation.

        Releases retry tokens back to the retry quota based on the previous amount
        consumed.

        :param token: The token used for the previous successful attempt.
        """
        await self._retry_quota.release(release_amount=token.last_quota_acquired)


class StandardRetryQuota:
    """Retry quota used by :py:class:`StandardRetryStrategy`."""

    INITIAL_RETRY_TOKENS = 500
    RETRY_COST = 5
    NO_RETRY_INCREMENT = 1
    TIMEOUT_RETRY_COST = 10

    def __init__(self):
        self._max_capacity = self.INITIAL_RETRY_TOKENS
        self._available_capacity = self.INITIAL_RETRY_TOKENS
        self._lock = asyncio.Lock()

    async def acquire(self, *, error: Exception) -> int:
        """Attempt to acquire a certain amount of capacity.

        If there's no sufficient amount of capacity available, raise an exception.
        Otherwise, we return the amount of capacity successfully allocated.
        """
        # TODO: update `is_timeout` when `is_timeout_error` is implemented
        is_timeout = False
        capacity_amount = self.TIMEOUT_RETRY_COST if is_timeout else self.RETRY_COST

        async with self._lock:
            if capacity_amount > self._available_capacity:
                raise RetryError("Retry quota exceeded")
            self._available_capacity -= capacity_amount
            return capacity_amount

    async def release(self, *, release_amount: int) -> None:
        """Release capacity back to the retry quota.

        The capacity being released will be truncated if necessary to ensure the max
        capacity is never exceeded.
        """
        increment = self.NO_RETRY_INCREMENT if release_amount == 0 else release_amount

        if self._available_capacity == self._max_capacity:
            return

        async with self._lock:
            self._available_capacity = min(
                self._available_capacity + increment, self._max_capacity
            )


class RetryStrategyMode(Enum):
    """Enumeration of available retry strategies."""

    SIMPLE = "simple"
    STANDARD = "standard"


RETRY_MODE_MAP = {
    RetryStrategyMode.SIMPLE: SimpleRetryStrategy,
    RetryStrategyMode.STANDARD: StandardRetryStrategy,
}
