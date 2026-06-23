#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import ExponentialBackoffJitterType as EBJT
from smithy_core.retries import (
    ExponentialRetryBackoffStrategy,
    StandardRetryQuota,
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


@pytest.fixture
def retry_quota() -> StandardRetryQuota:
    return StandardRetryQuota(initial_capacity=10)


def test_retry_quota_initial_state(
    retry_quota: StandardRetryQuota,
) -> None:
    assert retry_quota.available_capacity == 10


def test_retry_quota_acquire_success(
    retry_quota: StandardRetryQuota,
) -> None:
    acquired = retry_quota.acquire(error=Exception())
    assert retry_quota.available_capacity == 10 - acquired


def test_retry_quota_acquire_when_exhausted(
    retry_quota: StandardRetryQuota,
) -> None:
    # Drain capacity until insufficient for next acquire
    retry_quota.acquire(error=Exception())
    retry_quota.acquire(error=Exception())

    # Not enough capacity for another retry (need 5, only 0 left)
    with pytest.raises(RetryError, match="Retry quota exceeded"):
        retry_quota.acquire(error=Exception())


def test_retry_quota_release_restores_capacity(
    retry_quota: StandardRetryQuota,
) -> None:
    acquired = retry_quota.acquire(error=Exception())
    retry_quota.release(release_amount=acquired)
    assert retry_quota.available_capacity == 10


def test_retry_quota_release_zero_adds_increment(
    retry_quota: StandardRetryQuota,
) -> None:
    retry_quota.acquire(error=Exception())
    assert retry_quota.available_capacity == 5
    retry_quota.release(release_amount=0)
    assert retry_quota.available_capacity == 6


def test_retry_quota_release_caps_at_max(
    retry_quota: StandardRetryQuota,
) -> None:
    # Drain some capacity
    retry_quota.acquire(error=Exception())
    # Release more than we acquired. Should cap at initial capacity.
    retry_quota.release(release_amount=50)
    assert retry_quota.available_capacity == 10


def test_retry_quota_acquire_timeout_error(
    retry_quota: StandardRetryQuota,
) -> None:
    timeout_error = CallError(is_timeout_error=True, is_retry_safe=True)
    acquired = retry_quota.acquire(error=timeout_error)
    assert acquired == StandardRetryQuota.TIMEOUT_RETRY_COST
    assert retry_quota.available_capacity == 0
