#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from functools import lru_cache
from typing import Any

from ..exceptions import RetryError
from ..interfaces import retries as retries_interface
from ..retries import (
    ExponentialBackoffJitterType,
    ExponentialRetryBackoffStrategy,
    RetryStrategyOptions,
    RetryStrategyType,
    SimpleRetryToken,
    StandardRetryQuota,
    StandardRetryToken,
)
from .interfaces.retries import RetryStrategy


class RetryStrategyResolver:
    """Retry strategy resolver that caches retry strategies based on configuration options.

    This resolver caches retry strategy instances based on their configuration to reuse existing
    instances of RetryStrategy with the same settings. Uses LRU cache for thread-safe caching.
    """

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

    @lru_cache
    def _create_retry_strategy(
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
