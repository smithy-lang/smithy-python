#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import ExponentialBackoffJitterType as EBJT
from smithy_core.retries import (
    ExponentialRetryBackoffStrategy,
    SimpleRetryStrategy,
    StandardRetryQuota,
    StandardRetryStrategy,
)


@pytest.mark.parametrize(
    "jitter_type, scale_value, max_backoff, expected_delays",
    [
        # no jitter
        (EBJT.NONE, 2, 20, [0, 2.0, 4.0, 8.0, 16.0, 20.0, 20.0]),
        (EBJT.NONE, 2.0, 20.0, [0, 2.0, 4.0, 8.0, 16.0, 20.0, 20.0]),
        (EBJT.NONE, 1.0, 20.0, [0, 1.0, 2.0, 4.0, 8.0, 16.0, 20.0]),
        (EBJT.NONE, 4.0, 2.0, [0, 2.0, 2.0, 2.0]),
        (EBJT.NONE, 23.4, 76.5, [0, 23.4, 46.8, 76.5, 76.5]),
        # full jitter
        (EBJT.FULL, 2.0, 20.0, [0, 1.0, 2.0, 4.0, 8.0, 10.0, 10.0]),
        (EBJT.FULL, 5.0, 20.0, [0, 2.5, 5.0, 10.0, 10.0]),
        (EBJT.FULL, 5.0, 10.0, [0, 2.5, 5.0, 5.0, 5.0]),
        (EBJT.FULL, 23.4, 76.5, [0, 11.7, 23.4, 38.25, 38.25]),
        # equal jitter
        (EBJT.DEFAULT, 2.0, 20.0, [0, 1.5, 3.0, 6.0, 12.0, 15.0, 15.0]),
        (EBJT.DEFAULT, 23.4, 76.5, [0, 17.55, 35.1, 57.375, 57.375]),
        # decorrelated jitter
        (EBJT.DECORRELATED, 2.0, 20.0, [0, 5.0, 9.5, 16.25, 20.0, 20.0]),
        (EBJT.DECORRELATED, 23.4, 76.5, [0, 58.5, 76.5, 76.5]),
        # edge cases with zeros
        (EBJT.NONE, 5.0, 0.0, [0, 0, 0, 0]),
        (EBJT.NONE, 0.0, 5.0, [0, 0, 0, 0]),
        (EBJT.NONE, 0.0, 0.0, [0, 0, 0, 0]),
        (EBJT.FULL, 5.0, 0.0, [0, 0, 0, 0]),
        (EBJT.FULL, 0.0, 5.0, [0, 0, 0, 0]),
        (EBJT.FULL, 0.0, 0.0, [0, 0, 0, 0]),
    ],
)
def test_exponential_backoff_strategy(
    jitter_type: EBJT,
    scale_value: float,
    max_backoff: float,
    expected_delays: list[float],
) -> None:
    bos = ExponentialRetryBackoffStrategy(
        backoff_scale_value=scale_value,
        max_backoff=max_backoff,
        jitter_type=jitter_type,
        random=lambda: 0.5,  # every generated "random" value equals 0.5
    )

    for delay_index, delay_expected in enumerate(expected_delays):
        delay_actual = bos.compute_next_backoff_delay(retry_attempt=delay_index)
        assert delay_actual == pytest.approx(delay_expected)  # type: ignore


@pytest.mark.asyncio
@pytest.mark.parametrize("max_attempts", [2, 3, 10])
async def test_simple_retry_strategy(max_attempts: int) -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=max_attempts,
    )
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
async def test_simple_retry_does_not_retry_unclassified() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=Exception()
        )


@pytest.mark.asyncio
async def test_simple_retry_does_not_retry_when_safety_unknown() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(is_retry_safe=None)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
async def test_simple_retry_does_not_retry_unsafe() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(fault="client", is_retry_safe=False)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
@pytest.mark.parametrize("max_attempts", [2, 3, 10])
async def test_standard_retry_strategy(max_attempts: int) -> None:
    strategy = StandardRetryStrategy(max_attempts=max_attempts)
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
async def test_standard_retry_does_not_retry_unclassified() -> None:
    strategy = StandardRetryStrategy()
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=Exception()
        )


@pytest.mark.asyncio
async def test_standard_retry_does_not_retry_when_safety_unknown() -> None:
    strategy = StandardRetryStrategy()
    error = CallError(is_retry_safe=None)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
async def test_standard_retry_does_not_retry_unsafe() -> None:
    strategy = StandardRetryStrategy()
    error = CallError(fault="client", is_retry_safe=False)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
async def test_standard_retry_strategy_respects_max_attempts() -> None:
    strategy = StandardRetryStrategy()
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


@pytest.mark.asyncio
async def test_retry_after_overrides_backoff() -> None:
    strategy = StandardRetryStrategy()
    error = CallError(is_retry_safe=True, retry_after=5)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 5


@pytest.mark.asyncio
async def test_retry_quota_acquire_when_exhausted(monkeypatch) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 5, raising=False)
    monkeypatch.setattr(StandardRetryQuota, "RETRY_COST", 2, raising=False)

    quota = StandardRetryQuota()
    assert quota._available_capacity == 5

    # First acquire: 5 -> 3
    assert await quota.acquire(error=Exception()) == 2
    assert quota._available_capacity == 3

    # Second acquire: 3 -> 1
    assert await quota.acquire(error=Exception()) == 2
    assert quota._available_capacity == 1

    # Third acquire needs 2 but only 1 remains -> should raise
    with pytest.raises(RetryError):
        await quota.acquire(error=Exception())
    assert quota._available_capacity == 1


@pytest.mark.asyncio
async def test_retry_quota_release_zero_adds_increment(monkeypatch) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 5, raising=False)
    monkeypatch.setattr(StandardRetryQuota, "RETRY_COST", 2, raising=False)
    monkeypatch.setattr(StandardRetryQuota, "NO_RETRY_INCREMENT", 1, raising=False)

    quota = StandardRetryQuota()
    assert quota._available_capacity == 5

    # First acquire: 5 -> 3
    assert await quota.acquire(error=Exception()) == 2
    assert quota._available_capacity == 3

    # release 0 should add NO_RETRY_INCREMENT: 3 -> 4
    await quota.release(release_amount=0)
    assert quota._available_capacity == 4

    # Next acquire should still work: 4 -> 2
    assert await quota.acquire(error=Exception()) == 2
    assert quota._available_capacity == 2


@pytest.mark.asyncio
async def test_retry_quota_release_caps_at_max(monkeypatch) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 10, raising=False)
    monkeypatch.setattr(StandardRetryQuota, "RETRY_COST", 3, raising=False)

    quota = StandardRetryQuota()
    assert quota._available_capacity == 10

    # Drain some capacity: 10 -> 7 -> 4
    assert await quota.acquire(error=Exception()) == 3
    assert quota._available_capacity == 7
    assert await quota.acquire(error=Exception()) == 3
    assert quota._available_capacity == 4

    # Release more than needed: 4 + 8 = 12. Should cap at max = 10
    await quota.release(release_amount=8)
    assert quota._available_capacity == 10

    # Another acquire should succeed from max: 10 -> 7
    assert await quota.acquire(error=Exception()) == 3
    assert quota._available_capacity == 7


@pytest.mark.asyncio
async def test_retry_quota_releases_last_acquired_amount(monkeypatch) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 10, raising=False)
    monkeypatch.setattr(StandardRetryQuota, "RETRY_COST", 5, raising=False)

    strategy = StandardRetryStrategy()
    err = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()

    # Two retries: 10 -> 5 -> 0
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=err
    )
    assert strategy._retry_quota._available_capacity == 5
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=err
    )
    assert strategy._retry_quota._available_capacity == 0

    # Success returns ONLY the last acquired amount -> 5
    await strategy.record_success(token=token)
    assert strategy._retry_quota._available_capacity == 5


@pytest.mark.asyncio
async def test_retry_quota_release_when_no_retry(monkeypatch) -> None:
    monkeypatch.setattr(StandardRetryQuota, "INITIAL_RETRY_TOKENS", 10, raising=False)
    quota = StandardRetryQuota()

    await quota.acquire(error=Exception())
    assert quota._available_capacity == 5
    before = quota._available_capacity

    await quota.release(release_amount=0)
    # Should increment by NO_RETRY_INCREMENT = 1
    assert quota._available_capacity == min(before + 1, quota._max_capacity)
    assert quota._available_capacity == 6
