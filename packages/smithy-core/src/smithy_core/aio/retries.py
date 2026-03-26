#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio

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


class TokenBucketRetryStrategy(aio_retries_interface.RetryStrategy):
    def __init__(
        self,
        *,
        backoff_strategy: retries_interface.RetryBackoffStrategy | None = None,
        max_attempts: int = 5,
        token_bucket_capacity: int = 500,
        success_increment: int = 1,
        retry_cost: int = 14,
        throttling_retry_cost: int = 5,
        wait_on_empty: bool = False,
    ):
        """Retry strategy that rate limits on the client side using a token bucket.

        :param backoff_strategy: The backoff strategy used by returned tokens to compute
            the retry delay. Defaults to
            :py:class:`~smithy_core.retries.ExponentialRetryBackoffStrategy`.
        :param max_attempts: Upper limit on total number of attempts made, including
            initial attempt and retries.
        :param token_bucket_capacity: The maximum and initial capacity of the token
            bucket.
        :param success_increment: The number of tokens to put in the bucket upon a
            successful request.
        :param retry_cost: The number of tokens required to retry after a normal error.
        :param throttling_retry_cost: The number of tokens required to retry after a
            throttling error.
        :param wait_on_empty: Whether to wait for the bucket to fill when it empty or
            to fast-fail the request.

        :raises RetryError: If no further retry attempts are allowed.
        """
        from ..retries import ExponentialRetryBackoffStrategy

        self.backoff_strategy = backoff_strategy or ExponentialRetryBackoffStrategy()
        self.max_attempts = max_attempts
        self._token_bucket = TokenBucket(max_capacity=token_bucket_capacity)
        self._success_increment = success_increment
        self._retry_cost = retry_cost
        self._throttling_retry_cost = throttling_retry_cost
        self._wait_on_empty = wait_on_empty

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> retries_interface.RetryToken:
        retry_delay = self.backoff_strategy.compute_next_backoff_delay(0)
        return SimpleRetryToken(retry_count=0, retry_delay=retry_delay)

    async def refresh_retry_token_for_retry(
        self, *, token_to_renew: retries_interface.RetryToken, error: Exception
    ) -> retries_interface.RetryToken:
        if isinstance(error, retries_interface.ErrorRetryInfo) and error.is_retry_safe:
            attempt = token_to_renew.retry_count + 1
            if attempt >= self.max_attempts:
                raise RetryError(
                    f"Reached maximum number of allowed attempts: {self.max_attempts}"
                ) from error
            cost = (
                self._throttling_retry_cost
                if error.is_throttling_error
                else self._retry_cost
            )
            if await self._token_bucket.drain(cost, self._wait_on_empty):
                retry_delay = self.backoff_strategy.compute_next_backoff_delay(attempt)
                return SimpleRetryToken(retry_count=attempt, retry_delay=retry_delay)
            else:
                raise RetryError(
                    "The token bucket was empty, so no additional retries "
                    "were permitted."
                ) from error
        else:
            raise RetryError(f"Error is not retryable: {error}") from error

    async def record_success(self, *, token: retries_interface.RetryToken) -> None:
        await self._token_bucket.fill(self._success_increment)


class TokenBucket:
    def __init__(self, max_capacity: int = 500):
        """A token bucket intended to limit the retry rate of a client.

        :param max_capacity: The maximum capacity of the bucket. Default is 500.
        """
        self._max_capacity = max_capacity
        self._tokens = max_capacity
        self._token_lock = asyncio.Lock()
        self._token_condition = asyncio.Condition(self._token_lock)

    async def drain(self, count: int, wait_on_empty: bool = False) -> bool:
        """Attempt to consume the specified amount of tokens.

        :param count: The number of tokens to attempt to consume from the bucket.
            This value must be greater than 0 and less than the maximum capacity of
            the bucket.
        :param wait_on_empty: Whether to wait for the bucket to have the requested
            capacity.

        :returns: True if the tokens were able to be consumed, otherwise False.
        """
        if count <= 0:
            raise ValueError(f"Count must be greater than 0, but was {count}.")
        if count > self._max_capacity:
            raise ValueError(
                f"Cannot consume {count} tokens from bucket with maximum capacity "
                f"of {self._max_capacity}."
            )

        if wait_on_empty:
            # Use the Condition to acquire the lock if the intent is to wait for the
            # bucket to have the intended capacity.
            async with self._token_condition:
                # If the bucket already has the requested capacity, consume it
                # immediately rather than calling wait.
                if self._tokens >= count:
                    self._tokens -= count
                else:
                    # Otherwise wait for the requested capacity.
                    await self._token_condition.wait_for(lambda: self._tokens >= count)
                    self._tokens -= count
            return True

        # If there is no need to wait for the requested capacity, simply acquire the
        # lock directly and check.
        async with self._token_lock:
            if self._tokens >= count:
                self._tokens -= count
                return True
            return False

    async def fill(self, count: int) -> None:
        """Add a specified number of tokens to the bucket.

        :param count: The number of tokens to add to the bucket. This value must be
            greater than 0.
        """
        if count <= 0:
            raise ValueError(f"Count must be greater than 0, but was {count}.")

        async with self._token_condition:
            # Fill tokens, capped at the max capacity.
            self._tokens = min(self._max_capacity, self._tokens + count)

            # Notify any conditions waiting on the capacity to fill.
            self._token_condition.notify_all()
