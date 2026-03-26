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
