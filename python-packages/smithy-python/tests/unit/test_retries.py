# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import pytest

from smithy_python._private.retries import ExponentialBackoffJitterType as EBJT
from smithy_python._private.retries import (
    ExponentialRetryBackoffStrategy,
    SimpleRetryStrategy,
)
from smithy_python.exceptions import SmithyRetryException
from smithy_python.interfaces.retries import RetryErrorInfo, RetryErrorType


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
        delay_expected2 = delay_expected
        print(f"{delay_index=} {delay_actual=} {delay_expected2=}")
        assert delay_actual == pytest.approx(delay_expected)


@pytest.mark.parametrize("max_attempts", [2, 3, 10])
def test_simple_retry_strategy(max_attempts: int) -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=max_attempts,
    )
    error_info = RetryErrorInfo(error_type=RetryErrorType.THROTTLING)
    token = strategy.acquire_initial_retry_token()
    for _ in range(max_attempts - 1):
        token = strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error_info=error_info
        )
    with pytest.raises(SmithyRetryException):
        strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error_info=error_info
        )
