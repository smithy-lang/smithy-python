# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import StandardRetryQuota, StandardRetryStrategy


def get_retry_quota(strategy: StandardRetryStrategy) -> int:
    return strategy._retry_quota.available_capacity  # pyright: ignore[reportPrivateUsage]


async def test_standard_retry_eventually_succeeds() -> None:
    strategy = StandardRetryStrategy(max_attempts=3)
    error = CallError(is_retry_safe=True)

    token = await strategy.acquire_initial_retry_token()
    assert token.retry_count == 0
    assert get_retry_quota(strategy) == 500

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_count == 1
    assert get_retry_quota(strategy) == 495

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_count == 2
    assert get_retry_quota(strategy) == 490

    await strategy.record_success(token=token)
    assert get_retry_quota(strategy) == 495


async def test_standard_retry_fails_due_to_max_attempts() -> None:
    strategy = StandardRetryStrategy(max_attempts=3)
    error = CallError(is_retry_safe=True)

    token = await strategy.acquire_initial_retry_token()

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_count == 1
    assert get_retry_quota(strategy) == 495

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_count == 2
    assert get_retry_quota(strategy) == 490

    with pytest.raises(RetryError, match="maximum number of allowed attempts"):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert get_retry_quota(strategy) == 490


async def test_retry_quota_exhausted_after_single_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 5, raising=False)
    strategy = StandardRetryStrategy(max_attempts=3)
    error = CallError(is_retry_safe=True)

    token = await strategy.acquire_initial_retry_token()
    assert get_retry_quota(strategy) == 5

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_count == 1
    assert get_retry_quota(strategy) == 0

    with pytest.raises(RetryError, match="Retry quota exceeded"):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert get_retry_quota(strategy) == 0


async def test_retry_quota_prevents_retries_when_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 0, raising=False)
    strategy = StandardRetryStrategy(max_attempts=3)
    error = CallError(is_retry_safe=True)

    token = await strategy.acquire_initial_retry_token()
    assert get_retry_quota(strategy) == 0

    with pytest.raises(RetryError, match="Retry quota exceeded"):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert get_retry_quota(strategy) == 0


async def test_retry_quota_stops_retries_when_exhauste(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 10, raising=False)
    strategy = StandardRetryStrategy(max_attempts=5)
    error = CallError(is_retry_safe=True)

    token = await strategy.acquire_initial_retry_token()
    assert get_retry_quota(strategy) == 10

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert get_retry_quota(strategy) == 5

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert get_retry_quota(strategy) == 0

    with pytest.raises(RetryError, match="Retry quota exceeded"):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert get_retry_quota(strategy) == 0


async def test_retry_quota_recovers_after_successful_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 15, raising=False)
    strategy = StandardRetryStrategy(max_attempts=5)
    error = CallError(is_retry_safe=True)

    # First operation: 2 retries then success
    token = await strategy.acquire_initial_retry_token()
    assert get_retry_quota(strategy) == 15

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert get_retry_quota(strategy) == 10

    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert get_retry_quota(strategy) == 5

    await strategy.record_success(token=token)
    assert get_retry_quota(strategy) == 10

    # Second operation: 1 retry then success
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert get_retry_quota(strategy) == 5
    await strategy.record_success(token=token)
    assert get_retry_quota(strategy) == 10


async def test_retry_quota_shared_correctly_across_multiple_operations() -> None:
    strategy = StandardRetryStrategy(max_attempts=5)
    error = CallError(is_retry_safe=True)

    # Operation 1
    op1_token = await strategy.acquire_initial_retry_token()
    assert get_retry_quota(strategy) == 500

    op1_token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=op1_token, error=error
    )
    assert get_retry_quota(strategy) == 495

    op1_token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=op1_token, error=error
    )
    assert get_retry_quota(strategy) == 490

    # Operation 2 (while operation 1 is in progress)
    op2_token = await strategy.acquire_initial_retry_token()
    op2_token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=op2_token, error=error
    )
    assert get_retry_quota(strategy) == 485

    await strategy.record_success(token=op2_token)
    assert get_retry_quota(strategy) == 490

    await strategy.record_success(token=op1_token)
    assert get_retry_quota(strategy) == 495
