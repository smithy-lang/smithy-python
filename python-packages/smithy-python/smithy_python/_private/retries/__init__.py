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

import random
from datetime import timedelta
from enum import Enum
from typing import Callable

from ...interfaces.retries import (
    RetryBackoffStrategy,
    RetryErrorInfo,
    RetryStrategy,
    RetryToken,
)


class ExponentialBackoffJitterType(Enum):
    """
    Jitter mode for exponential backoff.

    """

    DEFAULT = 1  # "equal jitter" in blog post
    NONE = 2
    FULL = 3
    DECORRELATED = 4


class ExponentialRetryBackoffStrategy(RetryBackoffStrategy):
    """Exponential backoff with optional jitter

    See also: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    """

    def __init__(
        self,
        backoff_scale_value: timedelta,
        max_backoff: timedelta = timedelta(seconds=20),
        jitter_type: ExponentialBackoffJitterType = ExponentialBackoffJitterType.DEFAULT,
        random: Callable[[], float] = random.random,
    ):
        self._backoff_scale_value = backoff_scale_value
        self._max_backoff = max_backoff
        self._jitter_type = jitter_type
        self._random = random
        self._previous_delay_seconds = backoff_scale_value.total_seconds()

    def compute_next_backoff_delay(self, retry_attempt: int) -> timedelta:
        """Calculates truncated binary exponential backoff delay with with jitter::

            t_i = min(rand(0, 1) * scale ** attempt, max_backoff)

        where ``t_i`` is the backoff delay for the 0-based request attempt count ``i``.
        """
        if self._jitter_type == ExponentialBackoffJitterType.NONE:
            seconds = self._next_delay_no_jitter(retry_attempt=retry_attempt)
        elif self._jitter_type == ExponentialBackoffJitterType.DEFAULT:
            seconds = self._next_delay_equal_jitter(retry_attempt=retry_attempt)
        elif self._jitter_type == ExponentialBackoffJitterType.FULL:
            seconds = self._next_delay_full_jitter(retry_attempt=retry_attempt)
        elif self._jitter_type == ExponentialBackoffJitterType.DECORRELATED:
            seconds = self._next_delay_decorrelated_jitter(
                previous_delay=self._previous_delay_seconds
            )

        self._previous_delay_seconds = seconds
        return timedelta(seconds=seconds)

    def _base_delay(self, retry_attempt: int) -> float:
        return self._backoff_scale_value.total_seconds() * (2.0**retry_attempt)

    def _next_delay_no_jitter(self, retry_attempt: int) -> float:
        """Calculates truncated binary exponential backoff delay without jitter:

        t_i = min(cap, base * 2 ** attempt)
        """
        no_jitter_delay = self._base_delay(retry_attempt)
        return min(no_jitter_delay, self._max_backoff.total_seconds())

    def _next_delay_full_jitter(self, retry_attempt: int) -> float:
        """Calculates truncated binary exponential backoff delay with full jitter:

        t_i = random_between(max_backoff, min(cap, base * 2 ** attempt))
        """
        no_jitter_delay = self._base_delay(retry_attempt)
        return self._random() * min(no_jitter_delay, self._max_backoff.total_seconds())

    def _next_delay_equal_jitter(self, retry_attempt: int) -> float:
        """Calculates truncated binary exponential backoff delay with equal jitter:

        temp = min(cap, base * 2 ** attempt)
        t_i = (temp / 2) + random_between(0, temp / 2)
        """
        no_jitter_delay = self._base_delay(retry_attempt)
        return (self._random() * 0.5 + 0.5) * min(
            no_jitter_delay, self._max_backoff.total_seconds()
        )

    def _next_delay_decorrelated_jitter(self, previous_delay: float) -> float:
        """Calculates truncated binary exp. backoff delay with decorrelated jitter:

        t_i = min(max_backoff, random_between(base, t_(i-1) * 3))
        """
        return min(
            self._backoff_scale_value.total_seconds()
            + self._random() * previous_delay * 3,
            self._max_backoff.total_seconds(),
        )


class StandardRetryToken(RetryToken):
    def __init__(self, *, attempts: int, backoff_strategy: RetryBackoffStrategy):
        self._attempts = attempts
        self._backoff_strategy = backoff_strategy

    def get_retry_count(self) -> int:
        """Retry count is the total number of attempts minus the initial attempt"""
        return self._attempts - 1

    def get_retry_delay(self) -> timedelta:
        return self._backoff_strategy.compute_next_backoff_delay(self.get_retry_count())


class StandardRetryStrategy(RetryStrategy):
    """A bucket-free and unscoped retry strategy with arbitrary backoff strategy"""

    def __init__(
        self, *, backoff_strategy: RetryBackoffStrategy, max_retries_base: int
    ):
        self._backoff_strategy = backoff_strategy
        self._max_retries = max_retries_base

    def acquire_retry_token(self, *, token_scope: str) -> RetryToken:
        return StandardRetryToken(attempts=1, backoff_strategy=self._backoff_strategy)

    def refresh_retry_token_for_retry(
        self, *, token_to_renew: RetryToken, error_info: RetryErrorInfo
    ) -> RetryToken:
        if token_to_renew.get_retry_count() >= self._max_retries:
            raise Exception()  # TODO: which exception type?
        return StandardRetryToken(
            attempts=token_to_renew.get_retry_count() + 2,
            backoff_strategy=self._backoff_strategy,
        )

    def record_success(self, *, token: RetryToken) -> None:
        pass
