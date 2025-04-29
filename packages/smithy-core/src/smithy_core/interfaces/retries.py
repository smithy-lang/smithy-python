#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class ErrorRetryInfo(Protocol):
    """A protocol for errors that have retry information embedded."""

    is_retry_safe: bool | None = None
    """Whether the error is safe to retry.

    A value of True does not mean a retry will occur, but rather that a retry is allowed
    to occur.

    A value of None indicates that there is not enough information available to
    determine if a retry is safe.
    """

    retry_after: float | None = None
    """The amount of time that should pass before a retry.

    Retry strategies MAY choose to wait longer.
    """

    is_throttling_error: bool = False
    """Whether the error is a throttling error."""


class RetryBackoffStrategy(Protocol):
    """Stateless strategy for computing retry delays based on retry attempt account."""

    def compute_next_backoff_delay(self, retry_attempt: int) -> float:
        """Calculate timespan in seconds to delay before next retry.

        :param retry_attempt: The index of the retry attempt that is about to be made
        after the delay. The initial attempt, before any retries, is index ``0``, the
        first retry attempt after the initial attempt failed is index ``1``, and so on.
        """
        ...


@dataclass(kw_only=True)
class RetryToken(Protocol):
    """Token issued by a :py:class:`RetryStrategy` for the next attempt."""

    retry_count: int
    """Retry count is the total number of attempts minus the initial attempt."""

    retry_delay: float
    """Delay in seconds to wait before the retry attempt."""


class RetryStrategy(Protocol):
    """Issuer of :py:class:`RetryToken`s."""

    backoff_strategy: RetryBackoffStrategy
    """The strategy used by returned tokens to compute delay duration values."""

    max_attempts: int
    """Upper limit on total attempt count (initial attempt plus retries)."""

    def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> RetryToken:
        """Called before any retries (for the first attempt at the operation).

        :param token_scope: An arbitrary string accepted by the retry strategy to
            separate tokens into scopes.
        :returns: A retry token, to be used for determining the retry delay, refreshing
            the token after a failure, and recording success after success.
        :raises RetryError: If the retry strategy has no available tokens.
        """
        ...

    def refresh_retry_token_for_retry(
        self, *, token_to_renew: RetryToken, error: Exception
    ) -> RetryToken:
        """Replace an existing retry token from a failed attempt with a new token.

        After a failed operation call, this method is called to exchange a retry token
        that was previously obtained by calling :py:func:`acquire_initial_retry_token`
        or this method with a new retry token for the next attempt. This method can
        either choose to allow another retry and send a new or updated token, or reject
        the retry attempt and raise the error.

        :param token_to_renew: The token used for the previous failed attempt.
        :param error: The error that triggered the need for a retry.
        :raises RetryError: If no further retry attempts are allowed.
        """
        ...

    def record_success(self, *, token: RetryToken) -> None:
        """Return token after successful completion of an operation.

        Upon successful completion of the operation, a user calls this function to
        record that the operation was successful.

        :param token: The token used for the previous successful attempt.
        """
        ...
