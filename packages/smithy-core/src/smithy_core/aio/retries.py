#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from ..exceptions import RetryError
from ..interfaces import retries as retries_interface
from ..retries import SimpleRetryToken
from .interfaces import retries as aio_retries_interface


class SimpleRetryStrategy(aio_retries_interface.RetryStrategy):
    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        max_attempts: int = 5,
    ):
        """Async basic retry strategy that simply invokes the given backoff strategy.

        :param backoff_strategy: The backoff strategy used by returned tokens to compute
        the retry delay. Defaults to
        :py:class:`~smithy_core.retries.ExponentialRetryBackoffStrategy`.

        :param max_attempts: Upper limit on total number of attempts made, including
        initial attempt and retries.
        """
        from ..retries import ExponentialRetryBackoffStrategy

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
