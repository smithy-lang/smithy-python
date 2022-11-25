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

from datetime import timedelta
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
    retry_after_hint: Optional[timedelta]
    """
    Protocol hint. This could come from HTTP's 'retry-after' header or similar
    mechanisms in other protocols.
    """


class RetryBackoffStrategy(Protocol):
    def compute_next_backoff_delay(self, retry_attempt: int) -> timedelta:
        """
        Returns a Timespan that a caller performing retries should use for delaying
        between retries.
        """
        ...


class RetryToken(Protocol):
    """
    RetryToken is an abstract representation. They encode information for use with
    subsequent calls to the retry strategy.
    """

    def __init__(self, *, attempts: int):
        ...

    def get_retry_count(self) -> int:
        ...

    def get_retry_delay(self) -> timedelta:
        ...


class RetryStrategy(Protocol):
    def __init__(
        self, *, backoff_strategy: RetryBackoffStrategy, max_retries_base: int
    ):
        ...

    def acquire_retry_token(self, *, token_scope: str) -> RetryToken:
        """
        Called before any retries (for the first call to the operation). It either
        returns a retry token or an error upon the failure to acquire a token prior.
        """
        ...

    def refresh_retry_token_for_retry(
        self, *, token_to_renew: RetryToken, error_info: RetryErrorInfo
    ) -> RetryToken:
        """
        After a failed operation call, this function is invoked to refresh the
        retryToken returned by acquireInitialRetryToken(). This function can
        either choose to allow another retry and send a new or updated token,
        or reject the retry attempt and report the error either in an exception
        or returning an error.
        """
        ...

    def record_success(self, *, token: RetryToken) -> None:
        """
        Upon successful completion of the operation, a user calls this function
        to record that the operation was successful.
        """
        ...
