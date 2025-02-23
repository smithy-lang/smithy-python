#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class RetryErrorType(Enum):
    """Classification of errors based on desired retry behavior."""

    TRANSIENT = 1
    """A connection level error such as a socket timeout, socket connect error, TLS
    negotiation timeout."""

    THROTTLING = 2
    """The server explicitly told the client to back off, for example with HTTP status
    429 or 503."""

    SERVER_ERROR = 3
    """A server error that should be retried and does not match the definition of
    ``THROTTLING``."""

    CLIENT_ERROR = 4
    """Doesn't count against any budgets.

    This could be something like a 401 challenge in HTTP.
    """


@dataclass(kw_only=True)
class RetryErrorInfo:
    """Container for information about a retryable error."""

    error_type: RetryErrorType
    """Classification of error based on desired retry behavior."""

    retry_after_hint: float | None = None
    """Protocol hint for computing the timespan to delay before the next retry.

    This could come from HTTP's 'retry-after' header or similar mechanisms in other
    protocols.
    """


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
        :raises SmithyRetryException: If the retry strategy has no available tokens.
        """
        ...

    def refresh_retry_token_for_retry(
        self, *, token_to_renew: RetryToken, error_info: RetryErrorInfo
    ) -> RetryToken:
        """Replace an existing retry token from a failed attempt with a new token.

        After a failed operation call, this method is called to exchange a retry token
        that was previously obtained by calling :py:func:`acquire_initial_retry_token`
        or this method with a new retry token for the next attempt. This method can
        either choose to allow another retry and send a new or updated token, or reject
        the retry attempt and raise the error as exception.

        :param token_to_renew: The token used for the previous failed attempt.

        :param error_info: If no further retry is allowed, this information is used to
        construct the exception.

        :raises SmithyRetryException: If no further retry attempts are allowed.
        """
        ...

    def record_success(self, *, token: RetryToken) -> None:
        """Return token after successful completion of an operation.

        Upon successful completion of the operation, a user calls this function to
        record that the operation was successful.

        :param token: The token used for the previous successful attempt.
        """
        ...
