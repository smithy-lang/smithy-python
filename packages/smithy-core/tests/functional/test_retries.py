# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import StandardRetryQuota, StandardRetryStrategy


def test_standard_retry_eventually_succeeds() -> None:
    retry_quota = StandardRetryQuota()
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    token = strategy.acquire_initial_retry_token()
    assert token.retry_count == 0
    assert retry_quota.available_capacity == 500

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert token.retry_count == 1
    assert retry_quota.available_capacity == 495

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert token.retry_count == 2
    assert retry_quota.available_capacity == 490

    strategy.record_success(token=token)
    assert retry_quota.available_capacity == 495


def test_standard_retry_fails_due_to_max_attempts() -> None:
    retry_quota = StandardRetryQuota()
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    token = strategy.acquire_initial_retry_token()

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert token.retry_count == 1
    assert retry_quota.available_capacity == 495

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert token.retry_count == 2
    assert retry_quota.available_capacity == 490

    with pytest.raises(RetryError, match="maximum number of allowed attempts"):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 490


def test_retry_quota_exhausted_after_single_retry() -> None:
    retry_quota = StandardRetryQuota(initial_capacity=5)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    token = strategy.acquire_initial_retry_token()
    assert retry_quota.available_capacity == 5

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert token.retry_count == 1
    assert retry_quota.available_capacity == 0

    with pytest.raises(RetryError, match="Retry quota exceeded"):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 0


def test_retry_quota_prevents_retries_when_zero() -> None:
    retry_quota = StandardRetryQuota(initial_capacity=0)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    token = strategy.acquire_initial_retry_token()
    assert retry_quota.available_capacity == 0

    with pytest.raises(RetryError, match="Retry quota exceeded"):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 0


def test_retry_quota_stops_retries_when_exhausted() -> None:
    retry_quota = StandardRetryQuota(initial_capacity=10)
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    token = strategy.acquire_initial_retry_token()
    assert retry_quota.available_capacity == 10

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 5

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 0

    with pytest.raises(RetryError, match="Retry quota exceeded"):
        strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 0


def test_retry_quota_recovers_after_successful_responses() -> None:
    retry_quota = StandardRetryQuota(initial_capacity=15)
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    # First operation: 2 retries then success
    token = strategy.acquire_initial_retry_token()
    assert retry_quota.available_capacity == 15

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 10

    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 5

    strategy.record_success(token=token)
    assert retry_quota.available_capacity == 10

    # Second operation: 1 retry then success
    token = strategy.acquire_initial_retry_token()
    token = strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert retry_quota.available_capacity == 5
    strategy.record_success(token=token)
    assert retry_quota.available_capacity == 10


async def test_retry_quota_shared_correctly_across_multiple_operations() -> None:
    retry_quota = StandardRetryQuota()
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=retry_quota)
    error = CallError(is_retry_safe=True)

    # Operation 1
    op1_token = strategy.acquire_initial_retry_token()
    assert retry_quota.available_capacity == 500

    op1_token = strategy.refresh_retry_token_for_retry(
        token_to_renew=op1_token, error=error
    )
    assert retry_quota.available_capacity == 495

    op1_token = strategy.refresh_retry_token_for_retry(
        token_to_renew=op1_token, error=error
    )
    assert retry_quota.available_capacity == 490

    # Operation 2 (while operation 1 is in progress)
    op2_token = strategy.acquire_initial_retry_token()
    op2_token = strategy.refresh_retry_token_for_retry(
        token_to_renew=op2_token, error=error
    )
    assert retry_quota.available_capacity == 485

    strategy.record_success(token=op2_token)
    assert retry_quota.available_capacity == 490

    strategy.record_success(token=op1_token)
    assert retry_quota.available_capacity == 495
