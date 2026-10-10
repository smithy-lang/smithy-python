# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from time import sleep

import pytest
from smithy_core.exceptions import CallError, ClientTimeoutError, RetryError
from smithy_core.interfaces import retries as retries_interface
from smithy_core.retries import (
    ExponentialBackoffJitterType,
    ExponentialRetryBackoffStrategy,
    SimpleRetryStrategy,
    StandardRetryQuota,
    StandardRetryStrategy,
)


def retry_operation(
    strategy: retries_interface.RetryStrategy,
    responses: list[int | Exception],
) -> tuple[str, int]:
    token = strategy.acquire_initial_retry_token()
    response_iter = iter(responses)

    while True:
        if token.retry_delay:
            sleep(token.retry_delay)

        response = next(response_iter)
        attempt = token.retry_count + 1

        if response == 200:
            strategy.record_success(token=token)
            return "success", attempt

        if isinstance(response, Exception):
            error = response
        else:
            error = CallError(
                fault="server" if response >= 500 else "client",
                message=f"HTTP {response}",
                is_retry_safe=response >= 500,
            )

        try:
            token = strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )
        except RetryError:
            raise error


def test_standard_retry_eventually_succeeds():
    quota = StandardRetryQuota(initial_capacity=500)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    result, attempts = retry_operation(strategy, [500, 500, 200])

    assert result == "success"
    assert attempts == 3
    assert quota.available_capacity == 486


def test_standard_retry_fails_due_to_max_attempts():
    quota = StandardRetryQuota(initial_capacity=500)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    with pytest.raises(CallError, match="502"):
        retry_operation(strategy, [502, 502, 502])

    assert quota.available_capacity == 472


def test_retry_quota_exhausted_after_single_retry():
    quota = StandardRetryQuota(initial_capacity=14)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    with pytest.raises(CallError, match="502"):
        retry_operation(strategy, [500, 502])

    assert quota.available_capacity == 0


def test_retry_quota_prevents_retries_when_quota_zero():
    quota = StandardRetryQuota(initial_capacity=0)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    with pytest.raises(CallError, match="500"):
        retry_operation(strategy, [500])

    assert quota.available_capacity == 0


def test_retry_quota_stops_retries_when_exhausted():
    quota = StandardRetryQuota(initial_capacity=20)
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=quota)

    with pytest.raises(CallError, match="502"):
        retry_operation(strategy, [500, 502])

    assert quota.available_capacity == 6


def test_retry_quota_recovers_after_successful_responses():
    quota = StandardRetryQuota(initial_capacity=30)
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=quota)

    retry_operation(strategy, [500, 502, 200])
    assert quota.available_capacity == 16

    retry_operation(strategy, [500, 200])
    assert quota.available_capacity == 16


def test_retry_quota_handles_timeout_errors():
    quota = StandardRetryQuota(initial_capacity=500)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    result, attempts = retry_operation(
        strategy, [ClientTimeoutError(), ClientTimeoutError(), 200]
    )

    assert result == "success"
    assert attempts == 3
    assert quota.available_capacity == 486


def test_simple_retry_eventually_succeeds():
    backoff = ExponentialRetryBackoffStrategy(
        backoff_scale_value=0,
        max_backoff=0,
        jitter_type=ExponentialBackoffJitterType.NONE,
    )
    strategy = SimpleRetryStrategy(max_attempts=3, backoff_strategy=backoff)

    result, attempts = retry_operation(strategy, [500, 200])

    assert result == "success"
    assert attempts == 2
