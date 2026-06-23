#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Protocol, runtime_checkable

from ...interfaces.retries import RetryBackoffStrategy, RetryToken


@runtime_checkable
class RetryStrategy(Protocol):
    """Issuer of :py:class:`RetryToken`s."""

    backoff_strategy: RetryBackoffStrategy
    """The strategy used by returned tokens to compute delay duration values."""

    max_attempts: int
    """Upper limit on total attempt count (initial attempt plus retries)."""

    async def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> RetryToken:
        """Create a base retry token for the start of a request.

        :param token_scope: An arbitrary string accepted by the retry strategy to
            separate tokens into scopes.
        :returns: A retry token, to be used for determining the retry delay, refreshing
            the token after a failure, and recording success after success.
        :raises RetryError: If the retry strategy has no available tokens.
        """
        ...

    async def refresh_retry_token_for_retry(
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

    async def record_success(self, *, token: RetryToken) -> None:
        """Return token after successful completion of an operation.

        Upon successful completion of the operation, a user calls this function to
        record that the operation was successful.

        :param token: The token used for the previous successful attempt.
        """
        ...
