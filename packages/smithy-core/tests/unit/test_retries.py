#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import sys
import threading
import time
from collections.abc import Callable, Coroutine, Iterator
from copy import deepcopy
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smithy_core.aio.client import RequestPipeline
from smithy_core.aio.retries import (
    AdaptiveRetryStrategy,
    ClientRateLimiter,
    RequestRateTracker,
    RetryStrategyResolver,
    TokenBucket,
)
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import (
    CubicCalculator,
    ExponentialRetryBackoffStrategy,
    RetryStrategyOptions,
    StandardRetryQuota,
)
from smithy_core.retries import ExponentialBackoffJitterType as EBJT


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
    return StandardRetryQuota(initial_capacity=28)


def test_retry_quota_initial_state(
    retry_quota: StandardRetryQuota,
) -> None:
    assert retry_quota.available_capacity == 28


def test_retry_quota_acquire_success(
    retry_quota: StandardRetryQuota,
) -> None:
    acquired = retry_quota.acquire(error=Exception())
    assert acquired == StandardRetryQuota.RETRY_COST
    assert retry_quota.available_capacity == 28 - acquired


def test_retry_quota_acquire_when_exhausted(
    retry_quota: StandardRetryQuota,
) -> None:
    # Drain capacity until insufficient for next acquire
    retry_quota.acquire(error=Exception())
    retry_quota.acquire(error=Exception())

    # Not enough capacity for another retry (need RETRY_COST, only 0 left)
    with pytest.raises(RetryError, match="Retry quota exceeded"):
        retry_quota.acquire(error=Exception())


def test_retry_quota_release_restores_capacity(
    retry_quota: StandardRetryQuota,
) -> None:
    acquired = retry_quota.acquire(error=Exception())
    retry_quota.release(release_amount=acquired)
    assert retry_quota.available_capacity == 28


def test_retry_quota_release_zero_adds_increment(
    retry_quota: StandardRetryQuota,
) -> None:
    retry_quota.acquire(error=Exception())
    assert retry_quota.available_capacity == 28 - StandardRetryQuota.RETRY_COST
    retry_quota.release(release_amount=0)
    assert (
        retry_quota.available_capacity
        == 28 - StandardRetryQuota.RETRY_COST + StandardRetryQuota.NO_RETRY_INCREMENT
    )


def test_retry_quota_release_caps_at_max(
    retry_quota: StandardRetryQuota,
) -> None:
    # Drain some capacity
    retry_quota.acquire(error=Exception())
    # Release more than we acquired. Should cap at initial capacity.
    retry_quota.release(release_amount=50)
    assert retry_quota.available_capacity == 28


def test_retry_quota_acquire_throttling_error(
    retry_quota: StandardRetryQuota,
) -> None:
    throttling_error = CallError(is_throttling_error=True, is_retry_safe=True)
    acquired = retry_quota.acquire(error=throttling_error)
    assert acquired == StandardRetryQuota.THROTTLING_RETRY_COST
    assert (
        retry_quota.available_capacity == 28 - StandardRetryQuota.THROTTLING_RETRY_COST
    )


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_initial_state(self):
        token_bucket = TokenBucket()
        assert token_bucket.current_capacity == 0
        assert token_bucket.max_capacity == token_bucket.MIN_CAPACITY
        assert token_bucket.fill_rate == token_bucket.MIN_FILL_RATE

    @pytest.mark.asyncio
    async def test_acquire_succeeds_immediately_within_capacity(self):
        token_bucket = TokenBucket(curr_capacity=1)

        with patch("smithy_core.aio.retries.asyncio.wait_for") as mock_wait_for:
            await token_bucket.acquire(1)
            mock_wait_for.assert_not_called()

        assert token_bucket.current_capacity == 0

    @pytest.mark.asyncio
    async def test_acquire_waits_when_capacity_insufficient(self):
        token_bucket = TokenBucket(fill_rate=100.0)
        await token_bucket.acquire(1)

        with patch(
            "smithy_core.aio.retries.asyncio.wait_for", wraps=asyncio.wait_for
        ) as mock_wait_for:
            await token_bucket.acquire(1)
            mock_wait_for.assert_called()

        assert token_bucket.current_capacity == 0.0

    @pytest.mark.asyncio
    async def test_update_bucket_updates_rate(self):
        token_bucket = TokenBucket(curr_capacity=1)

        await token_bucket.update_rate(5.0)
        assert token_bucket.fill_rate == 5.0
        assert token_bucket.max_capacity == 5.0
        assert token_bucket.current_capacity == 1.0

    @pytest.mark.asyncio
    async def test_rate_can_never_be_zero(self):
        token_bucket = TokenBucket()
        await token_bucket.update_rate(0.0)

        assert token_bucket.fill_rate == TokenBucket.MIN_FILL_RATE
        assert token_bucket.max_capacity == TokenBucket.MIN_CAPACITY

    @pytest.mark.asyncio
    async def test_refill_caps_at_max_capacity(self):
        # 100s at 4 tokens/s would refill 400 tokens, far more than the capacity of 4
        with patch("time.monotonic", side_effect=[0.0, 0.0, 100.0]):
            token_bucket = TokenBucket()
            await token_bucket.update_rate(4.0)
            with token_bucket._lock:  # type: ignore
                token_bucket._refill()  # type: ignore

        assert token_bucket.current_capacity == 4.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "actions,expected_capacity",
        [
            ([("acquire", 1)], 0.0),
            ([("acquire", 1), ("update", 4)], 1.0),
            ([("acquire", 1), ("update", 4), ("acquire", 1)], 3.0),
            ([("acquire", 1), ("update", 4), ("acquire", 1), ("acquire", 1)], 3.0),
        ],
    )
    async def test_multiple_refills_over_time(
        self, actions: list[tuple[str, int]], expected_capacity: float
    ):
        time_values = [0.0, 1.0, 1.0, 1.5, 1.5, 4.0, 4.0, 5.0]

        with patch("time.monotonic", side_effect=time_values):
            token_bucket = TokenBucket(curr_capacity=0, fill_rate=2.0)

            for action, value in actions:
                if action == "acquire":
                    await token_bucket.acquire(value)
                elif action == "update":
                    await token_bucket.update_rate(value)

            assert token_bucket.current_capacity == expected_capacity

    async def test_update_rate_wakes_waiting_acquirers(self):
        token_bucket = TokenBucket(fill_rate=0.01)

        acquired = False

        async def slow_acquire():
            nonlocal acquired
            await token_bucket.acquire(2.0)
            acquired = True

        task = asyncio.create_task(slow_acquire())

        # Let slow_acquire() start waiting
        await asyncio.sleep(0.05)
        assert not acquired

        await token_bucket.update_rate(100.0)
        await asyncio.sleep(0.1)
        assert acquired
        await task

    async def test_acquire_does_not_wait_past_timeout(self):
        # The bucket starts empty, and at the minimum fill rate a token takes 2s to
        # refill, far past the timeout
        token_bucket = TokenBucket(timeout=0.05)

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            await token_bucket.acquire(1)
        assert time.monotonic() - start < 1

    def test_acquire_works_across_event_loops(self):
        # A client, and so its bucket, can outlive the event loop it was first used on
        token_bucket = TokenBucket(fill_rate=20.0)

        async def contended_acquires():
            # The bucket starts empty, so both acquires have to wait
            await asyncio.gather(token_bucket.acquire(1), token_bucket.acquire(1))

        asyncio.run(contended_acquires())
        asyncio.run(contended_acquires())


class TestSharedAcrossThreads:
    """One client, and so one rate limiter, may be used from several threads at once,
    each running its own event loop."""

    _THREADS = 8

    @pytest.fixture
    def frequent_thread_switches(self) -> Iterator[None]:
        # Switch threads constantly so they collide inside the critical sections
        original = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        yield
        sys.setswitchinterval(original)

    def _run_in_threads(
        self, target: Callable[[], Coroutine[Any, Any, None]]
    ) -> list[BaseException]:
        errors: list[BaseException] = []

        def run() -> None:
            try:
                asyncio.run(target())
            except BaseException as e:
                errors.append(e)

        threads = [
            threading.Thread(target=run, daemon=True) for _ in range(self._THREADS)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            # A deadlock fails the test instead of hanging the suite
            thread.join(timeout=30)
            assert not thread.is_alive(), "thread did not finish"
        return errors

    def test_rate_tracker(self, frequent_thread_switches: None):
        tracker = RequestRateTracker()

        async def measure_many() -> None:
            for _ in range(3000):
                await tracker.measure_rate()

        assert self._run_in_threads(measure_many) == []

    def test_token_bucket_rate_updates_and_acquires(
        self, frequent_thread_switches: None
    ):
        bucket = TokenBucket(fill_rate=100000.0)

        async def update_and_acquire() -> None:
            await bucket.update_rate(100000.0)
            for _ in range(500):
                await bucket.acquire(1)
                assert bucket.current_capacity >= 0

        assert self._run_in_threads(update_and_acquire) == []

    def test_token_bucket_hands_out_each_token_once(
        self, frequent_thread_switches: None
    ):
        acquires_per_thread = 500
        # Exactly enough tokens for every acquire, so no thread has to wait
        bucket = TokenBucket(curr_capacity=self._THREADS * acquires_per_thread)

        async def spend() -> None:
            for _ in range(acquires_per_thread):
                await bucket.acquire(1)

        assert self._run_in_threads(spend) == []
        # A lost update to the count would leave tokens behind
        assert bucket.current_capacity < 1


class TestRateLimiter:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rate_limiter_enabled, current_bucket_capacity, expected_bucket_capacity_after_acquire",
        [
            (True, 2.0, 1.0),
            (False, 1.0, 1.0),
        ],
    )
    async def test_token_consumption_before_request_scenarios(
        self,
        rate_limiter_enabled: bool,
        current_bucket_capacity: float,
        expected_bucket_capacity_after_acquire: float,
    ):
        token_bucket = TokenBucket(curr_capacity=current_bucket_capacity)
        calculator = CubicCalculator(starting_max_rate=1.0, start_time=0.0)
        tracker = RequestRateTracker()

        limiter = ClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=calculator,
            rate_tracker=tracker,
            rate_limiter_enabled=rate_limiter_enabled,
        )

        await limiter.before_sending_request()
        assert token_bucket.current_capacity == expected_bucket_capacity_after_acquire

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "throttling_error, rate_limiter_enabled, measured_rate, expected_bucket_fill_rate",
        [
            (True, False, 5.0, 3.5),
            (True, True, 5.0, 0.5),
            (False, True, 5.0, 7.83),
            (False, False, 5.0, 7.83),
        ],
    )
    async def test_token_consumption_after_response_scenarios(
        self,
        throttling_error: bool,
        rate_limiter_enabled: bool,
        measured_rate: float,
        expected_bucket_fill_rate: float,
    ):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3]
            token_bucket = TokenBucket()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            tracker = RequestRateTracker()

            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=rate_limiter_enabled,
            )

            with patch.object(tracker, "measure_rate", return_value=measured_rate):
                await limiter.after_receiving_response(
                    throttling_error=throttling_error
                )

        assert round(token_bucket.fill_rate, 2) == expected_bucket_fill_rate

    async def test_throttling_response_enables_rate_limiter(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4]
            token_bucket = TokenBucket()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            tracker = RequestRateTracker()

            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=False,
            )

            await limiter.after_receiving_response(throttling_error=True)
        assert limiter.rate_limit_enabled is True

    async def test_raises_timeout_error_when_token_acquisition_takes_30_secs(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 31]
            token_bucket = TokenBucket(curr_capacity=1)
            calculator = CubicCalculator()
            tracker = RequestRateTracker()
            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=True,
            )

            await limiter.before_sending_request()
            with pytest.raises(TimeoutError):
                await limiter.before_sending_request()

    async def test_tokens_accumulation_after_numerous_successful_responses(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [i * 0.01 for i in range(5000)]
            token_bucket = TokenBucket(curr_capacity=1)
            calculator = CubicCalculator()
            tracker = RequestRateTracker()
            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=True,
            )

            await limiter.after_receiving_response(throttling_error=True)
            for _ in range(1000):
                await limiter.after_receiving_response(throttling_error=False)
            await limiter.after_receiving_response(throttling_error=True)

            # The final throttle caps the tokens saved up during the successes
            assert token_bucket.current_capacity < 25

    async def test_sending_rate_sequence(self):
        # Each step is (throttled, timestamp, expected measured rate, expected fill
        # rate of the bucket)
        steps = [
            (False, 0.2, 0.0, 0.5),
            (False, 0.4, 0.0, 0.5),
            (False, 0.6, 4.8, 0.5),
            (False, 0.8, 4.8, 0.5),
            (False, 1.0, 4.16, 0.5),
            (False, 1.2, 4.16, 0.6912),
            (False, 1.4, 4.16, 1.0976),
            (False, 1.6, 5.632, 1.6384),
            (False, 1.8, 5.632, 2.3328),
            (True, 2.0, 4.3264, 3.02848),
            (False, 2.2, 4.3264, 3.486639),
            (False, 2.4, 4.3264, 3.821874),
            (False, 2.6, 5.66528, 4.053386),
            (False, 2.8, 5.66528, 4.200373),
            (False, 3.0, 4.333056, 4.282037),
            (True, 3.2, 4.333056, 2.997426),
            (False, 3.4, 4.333056, 3.452226),
        ]
        now = 0.0
        with patch(
            "smithy_core.aio.retries.time", SimpleNamespace(monotonic=lambda: now)
        ):
            token_bucket = TokenBucket()
            tracker = RequestRateTracker()
            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=CubicCalculator(start_time=0.0),
                rate_tracker=tracker,
                rate_limiter_enabled=False,
            )

            for throttled, timestamp, measured_rate, fill_rate in steps:
                now = timestamp
                await limiter.after_receiving_response(throttling_error=throttled)

                assert tracker.measured_client_rate == pytest.approx(  # type: ignore
                    measured_rate, abs=1e-6
                )
                assert token_bucket.fill_rate == pytest.approx(fill_rate, abs=1e-6)  # type: ignore

    async def test_calculated_rate_is_capped_at_2x_measured_rate(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4]
            token_bucket = TokenBucket()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            tracker = RequestRateTracker()

            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=True,
            )

            with (
                patch.object(tracker, "measure_rate", return_value=5.0),
                patch.object(
                    calculator, "calculate_scaled_request_rate", return_value=20.0
                ),
                patch.object(token_bucket, "_set_rate") as mock_set_rate,
            ):
                await limiter.after_receiving_response(throttling_error=False)

                # calculated rate should be capped at 2x measured rate at 2 * 5.0 = 10.0
                mock_set_rate.assert_called_once_with(10.0)

    async def test_new_rate_is_set_while_holding_the_lock(self):
        # Two threads could otherwise calculate rates A then B but apply B then A
        token_bucket = TokenBucket()
        limiter = ClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=CubicCalculator(),
            rate_tracker=RequestRateTracker(),
            rate_limiter_enabled=True,
        )
        lock_held: list[bool] = []

        def record_lock(rate: float) -> None:
            lock_held.append(limiter._lock.locked())  # type: ignore[reportPrivateUsage]

        token_bucket._set_rate = record_lock  # type: ignore[method-assign]
        await limiter.after_receiving_response(throttling_error=True)
        await limiter.after_receiving_response(throttling_error=False)

        assert lock_held == [True, True]


class TestCubicCalculator:
    def test_cubic_calculator_initializes(self):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        assert calculator.last_max_rate == 10.0
        assert calculator.last_throttle_time == 5.0

    def test_calculate_inflection_point(self):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        time_window = calculator.calculate_and_update_inflection_point()
        assert round(time_window, 2) == 1.96

    @pytest.mark.parametrize(
        "cases",
        [
            # (response, timestamp, calculated_rate)
            [
                ("success", 5, 7.0),
                ("success", 6, 9.64893600966),
                ("success", 7, 10.000030849917364),
                ("success", 8, 10.453284520772092),
                ("success", 9, 13.408697022224185),
                ("success", 10, 21.26626835427364),
                ("success", 11, 36.425998516920465),
            ],
            [
                ("success", 5, 7.0),
                ("success", 6, 9.64893600966),
                ("throttle", 7, 6.754255206761999),
                ("throttle", 8, 4.727978644733399),
                ("success", 9, 6.606547753887045),
                ("success", 10, 6.763279816944947),
                ("success", 11, 7.598174833907107),
                ("success", 12, 11.511232804773524),
            ],
        ],
        ids=["successes", "successes_and_throttles"],
    )
    def test_rate_sequence_after_successes_and_throttles(
        self, cases: list[tuple[str, float, float]]
    ):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        current_rate = 10.0
        for response, timestamp, expected in cases:
            if response == "success":
                current_rate = calculator.calculate_scaled_request_rate(timestamp)
            else:
                current_rate = calculator.calculate_throttled_request_rate(
                    current_rate, timestamp
                )
            assert current_rate == pytest.approx(expected)  # type: ignore

    def test_throttle_request(self):
        calculator = CubicCalculator(starting_max_rate=10.0, start_time=5.0)
        result = calculator.calculate_throttled_request_rate(
            rate_to_use=8.0, timestamp=10.0
        )

        assert result == 8.0 * 0.7
        assert calculator.last_max_rate == 8.0
        assert calculator.last_throttle_time == 10.0


class TestRequestRateTracker:
    async def test_measure_rate_same_bucket(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.3, 0.4]
            tracker = RequestRateTracker()
            rate1 = await tracker.measure_rate()
            rate2 = await tracker.measure_rate()

        assert rate1 == 0
        assert rate2 == 0
        assert tracker.request_count == 2

    async def test_measure_rate_new_bucket(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.7]
            tracker = RequestRateTracker()

            await tracker.measure_rate()
            rate = await tracker.measure_rate()

            # 2 requests over a 0.5s bucket is 4 r/s, smoothed: 4 * 0.8 + 0 * 0.2
            assert rate == pytest.approx(3.2)  # type: ignore
            assert tracker.request_count == 0


class TestAdaptiveRetryStrategy:
    """Tests for AdaptiveRetryStrategy with rate limiting."""

    def test_initialization_with_default_rate_limiter(self):
        strategy = AdaptiveRetryStrategy()

        assert strategy.rate_limiter is not None
        assert isinstance(strategy.rate_limiter, ClientRateLimiter)
        assert strategy.rate_limiter.rate_limit_enabled is False

    def test_initialization_with_custom_rate_limiter(self):
        token_bucket = TokenBucket()
        calculator = CubicCalculator(starting_max_rate=5.0, start_time=0.0)
        tracker = RequestRateTracker()
        custom_limiter = ClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=calculator,
            rate_tracker=tracker,
            rate_limiter_enabled=True,
        )

        strategy = AdaptiveRetryStrategy(rate_limiter=custom_limiter)

        assert strategy.rate_limiter is custom_limiter
        assert strategy.rate_limiter.rate_limit_enabled is True

    @pytest.mark.parametrize(
        "error, expected",
        [
            (CallError(message="Throttled", is_throttling_error=True), True),
            (CallError(message="Server error", is_throttling_error=False), False),
            (Exception("Generic error"), False),
        ],
        ids=["throttling", "not_throttling", "not_a_call_error"],
    )
    def test_is_throttling_error(self, error: Exception, expected: bool):
        assert AdaptiveRetryStrategy().is_throttling_error(error) is expected

    @pytest.mark.asyncio
    async def test_resolver_creates_adaptive_strategy(self):
        resolver = RetryStrategyResolver()
        option1 = RetryStrategyOptions(retry_mode="adaptive")

        strategy = await resolver.resolve_retry_strategy(retry_strategy=option1)

        assert isinstance(strategy, AdaptiveRetryStrategy)
        assert strategy.max_attempts == 3

    @pytest.mark.parametrize("max_attempts", [2, 3, 10])
    async def test_adaptive_retry_strategy(self, max_attempts: int) -> None:
        strategy = AdaptiveRetryStrategy(max_attempts=max_attempts)
        error = CallError(is_retry_safe=True)
        token = await strategy.acquire_initial_retry_token()
        for _ in range(max_attempts - 1):
            token = await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    def test_deepcopy_returns_adaptive_strategy_with_rate_limiter(self) -> None:
        strategy = AdaptiveRetryStrategy()
        copied = deepcopy(strategy)

        assert copied is strategy
        assert isinstance(copied, AdaptiveRetryStrategy)
        assert copied.rate_limiter is strategy.rate_limiter


class TestRequestPipelineRateLimiting:
    def _non_retryable_call(self, strategy: AdaptiveRetryStrategy) -> Any:
        # A call whose input stream can't be resent, so it skips the retry loop
        call = MagicMock()
        call.retryable.return_value = False
        call.retry_strategy = strategy
        return call

    def _unseekable_request_context(self) -> Any:
        # The request's input stream can't be rewound, so it can't be resent
        context = MagicMock()
        context.transport_request.body.seekable.return_value = False
        return context

    def _adaptive_strategy_with_mocked_limiter(
        self,
    ) -> tuple[AdaptiveRetryStrategy, ClientRateLimiter]:
        limiter = ClientRateLimiter(
            token_bucket=TokenBucket(),
            cubic_calculator=CubicCalculator(),
            rate_tracker=RequestRateTracker(),
            rate_limiter_enabled=True,
        )
        limiter.before_sending_request = AsyncMock()  # type: ignore[method-assign]
        limiter.after_receiving_response = AsyncMock()  # type: ignore[method-assign]
        return AdaptiveRetryStrategy(rate_limiter=limiter), limiter

    @pytest.mark.asyncio
    async def test_non_retryable_call_applies_rate_limiting_on_success(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        handle_attempt = AsyncMock(
            return_value=SimpleNamespace(transport_response=MagicMock(), response="ok")
        )

        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            await pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy),
                self._unseekable_request_context(),
                None,
            )

        handle_attempt.assert_awaited_once()
        limiter.before_sending_request.assert_awaited_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_awaited_once_with(  # type: ignore[attr-defined]
            throttling_error=False
        )

    @pytest.mark.asyncio
    async def test_non_retryable_call_reports_throttle_without_retrying(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        error = CallError(is_retry_safe=True, is_throttling_error=True)
        handle_attempt = AsyncMock(
            return_value=SimpleNamespace(transport_response=MagicMock(), response=error)
        )

        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            output_context = await pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy),
                self._unseekable_request_context(),
                None,
            )

        # Sent once and returned as-is, even though the error is retry-safe
        handle_attempt.assert_awaited_once()
        assert output_context.response is error
        limiter.before_sending_request.assert_awaited_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_awaited_once_with(True)  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_failure_without_response_does_not_update_rate_limiter(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        # Fails before sending, e.g. endpoint resolution or signing, so no response
        error = CallError(message="Unable to resolve endpoint", is_retry_safe=False)
        handle_attempt = AsyncMock(
            return_value=SimpleNamespace(transport_response=None, response=error)
        )

        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            output_context = await pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy),
                self._unseekable_request_context(),
                None,
            )

        assert output_context.response is error
        limiter.before_sending_request.assert_awaited_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_not_awaited()  # type: ignore[attr-defined]
