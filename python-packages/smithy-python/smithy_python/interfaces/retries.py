# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from enum import Enum
from typing import Optional, Protocol


class RetryErrorType(Enum):
    TRANSIENT = 1
    """
    A connection level error such as a socket timeout, socket connect error, TLS
    negotiation timeout.
    """

    THROTTLING = 2
    """
    The server explicitly told the client to back off, for example with HTTP status 429
    or 503.
    """

    SERVER_ERROR = 3
    """
    A server error that should be retried and does not match the definition of
    `THROTTLING`.
    """

    CLIENT_ERROR = 4
    """
    Doesn't count against any budgets. This could be something like a 401 challenge in
    HTTP.
    """


class RetryErrorInfo(Protocol):
    error_type: RetryErrorType
    retry_after_hint: Optional[float]
    """Protocol hint for computing the timespan to delay before the next retry.

    This could come from HTTP's 'retry-after' header or similar mechanisms in other
    protocols.
    """


class RetryBackoffStrategy(Protocol):
    def compute_next_backoff_delay(self, retry_attempt: int) -> float:
        """Calculate timespan in seconds to delay before next retry.

        :param retry_attempt: The index of the attempt that is about to be made after
        the delay. The initial attempt, before any retries, is index ``0``, the first
        retry attempt after the initial attempt failed is index ``1``, and so on.
        """
        ...


class RetryToken(Protocol):
    """Token issued by a retry strategy. Contains information for subsequent calls."""

    def get_retry_count(self) -> int:
        ...

    def get_retry_delay(self) -> float:
        ...


class RetryStrategy(Protocol):
    backoff_strategy: RetryBackoffStrategy
    max_retries_base: int

    def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> RetryToken:
        """Called before any retries (for the first call to the operation).

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
        """Refresh the a token after a failed attempt.

        After a failed operation call, this function is invoked to refresh the
        retryToken returned by :py:func:`acquire_initial_retry_token`. This function
        can either choose to allow another retry and send a new or updated token,
        or reject the retry attempt and raise the error as exception.

        :param token_to_renew: The token used for the previous failed attempt.

        :param error_info: If no further retry is allowed, this information is used to
        construct the exception.

        :raises SmithyRetryException: If no further retry attempts are allowed.
        """
        ...

    def record_success(self, *, token: RetryToken) -> None:
        """Return token after successful completion of an operation.

        Upon successful completion of the operation, a user calls this function
        to record that the operation was successful.

        :param token: The token used for the previous successful attempt.
        """
        ...
