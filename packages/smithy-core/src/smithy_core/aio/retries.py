#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from functools import lru_cache
from typing import Any

from ..interfaces import retries as retries_interface
from ..retries import (
    RetryStrategyOptions,
    RetryStrategyType,
    SimpleRetryToken,
    StandardRetryQuota,
    StandardRetryToken,
)
from ..retries import SimpleRetryStrategy as _SyncSimpleRetryStrategy
from ..retries import StandardRetryStrategy as _SyncStandardRetryStrategy
from .interfaces.retries import RetryStrategy


class RetryStrategyResolver:
    """Resolves and caches asynchronous retry strategies from configuration options."""

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
        """Async wrapper over :py:class:`smithy_core.retries.SimpleRetryStrategy`.

        The retry decision is pure synchronous computation; this exposes it through the
        async ``RetryStrategy`` protocol the async pipeline awaits.

        :param backoff_strategy: The backoff strategy used by returned tokens to compute
            the retry delay. Defaults to :py:class:`ExponentialRetryBackoffStrategy`.
        :param max_attempts: Upper limit on total number of attempts made, including
            initial attempt and retries.
        """
        self._sync = _SyncSimpleRetryStrategy(
            backoff_strategy=backoff_strategy, max_attempts=max_attempts
        )
        self.backoff_strategy = self._sync.backoff_strategy
        self.max_attempts = self._sync.max_attempts

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> SimpleRetryToken:
        return self._sync.acquire_initial_retry_token(token_scope=token_scope)

    async def refresh_retry_token_for_retry(
        self, *, token_to_renew: retries_interface.RetryToken, error: Exception
    ) -> SimpleRetryToken:
        return self._sync.refresh_retry_token_for_retry(
            token_to_renew=token_to_renew, error=error
        )

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        self._sync.record_success(token=token)

    def __deepcopy__(self, memo: Any) -> "SimpleRetryStrategy":
        return self


class StandardRetryStrategy:
    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        throttling_backoff_strategy: retries_interface.RetryBackoffStrategy
        | None = None,
        max_attempts: int = 3,
        retry_quota: StandardRetryQuota | None = None,
    ):
        """Async wrapper over :py:class:`smithy_core.retries.StandardRetryStrategy`.

        The retry decision is pure synchronous computation; this exposes it through the
        async ``RetryStrategy`` protocol the async pipeline awaits.

        :param backoff_strategy: The backoff strategy used to compute the retry delay
            for non-throttling errors.
        :param throttling_backoff_strategy: The backoff strategy used to compute the
            retry delay for throttling errors.
        :param max_attempts: Upper limit on total number of attempts made, including
            initial attempt and retries.
        :param retry_quota: The retry quota to use for managing retry capacity.
        """
        self._sync = _SyncStandardRetryStrategy(
            backoff_strategy=backoff_strategy,
            throttling_backoff_strategy=throttling_backoff_strategy,
            max_attempts=max_attempts,
            retry_quota=retry_quota,
        )
        self.backoff_strategy = self._sync.backoff_strategy
        self.throttling_backoff_strategy = self._sync.throttling_backoff_strategy
        self.max_attempts = self._sync.max_attempts

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> StandardRetryToken:
        return self._sync.acquire_initial_retry_token(token_scope=token_scope)

    async def refresh_retry_token_for_retry(
        self, *, token_to_renew: retries_interface.RetryToken, error: Exception
    ) -> StandardRetryToken:
        return self._sync.refresh_retry_token_for_retry(
            token_to_renew=token_to_renew, error=error
        )

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        self._sync.record_success(token=token)

    def __deepcopy__(self, memo: Any) -> "StandardRetryStrategy":
        return self
