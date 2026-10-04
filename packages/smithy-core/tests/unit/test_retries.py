#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import sys
import threading
import time
from collections.abc import Callable, Iterator
from copy import deepcopy
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from smithy_core.client import RequestPipeline
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import (
    AdaptiveRetryStrategy,
    ClientRateLimiter,
    CubicCalculator,
    ExponentialRetryBackoffStrategy,
    RequestRateTracker,
    RetryStrategyOptions,
    RetryStrategyResolver,
    StandardRetryQuota,
    TokenBucket,
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
    def test_initial_state(self):
        token_bucket = TokenBucket()
        assert token_bucket.current_capacity == 0
        assert token_bucket.max_capacity == token_bucket.MIN_CAPACITY
        assert token_bucket.fill_rate == token_bucket.MIN_FILL_RATE

    def test_acquire_succeeds_immediately_within_capacity(self):
        token_bucket = TokenBucket(curr_capacity=1)
        with patch.object(token_bucket._condition, "wait") as mock_wait:  # type: ignore[reportPrivateUsage]
            token_bucket.acquire(1)
            mock_wait.assert_not_called()
        assert token_bucket.current_capacity == 0

    def test_acquire_waits_when_capacity_insufficient(self):
        token_bucket = TokenBucket(fill_rate=100.0)
        token_bucket.acquire(1)
        with patch.object(
            token_bucket._condition,  # type: ignore[reportPrivateUsage]
            "wait",
            wraps=token_bucket._condition.wait,  # type: ignore[reportPrivateUsage]
        ) as mock_wait:
            token_bucket.acquire(1)
            mock_wait.assert_called()
        assert token_bucket.current_capacity == 0.0

    def test_update_bucket_updates_rate(self):
        token_bucket = TokenBucket(curr_capacity=1)
        token_bucket.update_rate(5.0)
        assert token_bucket.fill_rate == 5.0
        assert token_bucket.max_capacity == 5.0
        assert token_bucket.current_capacity == 1.0

    def test_rate_can_never_be_zero(self):
        token_bucket = TokenBucket()
        token_bucket.update_rate(0.0)
        assert token_bucket.fill_rate == TokenBucket.MIN_FILL_RATE
        assert token_bucket.max_capacity == TokenBucket.MIN_CAPACITY

    def test_refill_caps_at_max_capacity(self):
        # 100s at 4 tokens/s would refill 400 tokens, far more than the capacity of 4
        with patch("time.monotonic", side_effect=[0.0, 0.0, 100.0]):
            token_bucket = TokenBucket()
            token_bucket.update_rate(4.0)
            with token_bucket._condition:  # type: ignore[reportPrivateUsage]
                token_bucket._refill()  # type: ignore[reportPrivateUsage]
        assert token_bucket.current_capacity == 4.0

    @pytest.mark.parametrize(
        "actions,expected_capacity",
        [
            ([("acquire", 1)], 0.0),
            ([("acquire", 1), ("update", 4)], 1.0),
            ([("acquire", 1), ("update", 4), ("acquire", 1)], 3.0),
            ([("acquire", 1), ("update", 4), ("acquire", 1), ("acquire", 1)], 3.0),
        ],
    )
    def test_multiple_refills_over_time(
        self, actions: list[tuple[str, int]], expected_capacity: float
    ):
        time_values = [0.0, 1.0, 1.0, 1.5, 1.5, 4.0, 4.0, 5.0]
        with patch("time.monotonic", side_effect=time_values):
            token_bucket = TokenBucket(curr_capacity=0, fill_rate=2.0)
            for action, value in actions:
                if action == "acquire":
                    token_bucket.acquire(value)
                elif action == "update":
                    token_bucket.update_rate(value)
            assert token_bucket.current_capacity == expected_capacity

    def test_update_rate_wakes_waiting_acquirers(self):
        token_bucket = TokenBucket(fill_rate=0.01)
        acquired = False

        def slow_acquire() -> None:
            nonlocal acquired
            token_bucket.acquire(2.0)
            acquired = True

        thread = threading.Thread(target=slow_acquire, daemon=True)
        thread.start()
        # Let slow_acquire() start waiting
        time.sleep(0.05)
        assert not acquired
        token_bucket.update_rate(100.0)
        thread.join(timeout=5)
        assert acquired

    def test_acquire_does_not_wait_past_timeout(self):
        # The bucket starts empty, and at the minimum fill rate a token takes 2s to
        # refill, far past the timeout
        token_bucket = TokenBucket(timeout=0.05)
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            token_bucket.acquire(1)
        assert time.monotonic() - start < 1


class TestSharedAcrossThreads:
    """One client, and so one rate limiter, may be used from several threads at once."""

    _THREADS = 8

    @pytest.fixture
    def frequent_thread_switches(self) -> Iterator[None]:
        # Switch threads constantly so they collide inside the critical sections
        original = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        yield
        sys.setswitchinterval(original)

    def _run_in_threads(self, target: Callable[[], None]) -> list[BaseException]:
        errors: list[BaseException] = []

        def run() -> None:
            try:
                target()
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

        def measure_many() -> None:
            for _ in range(3000):
                tracker.measure_rate()

        assert self._run_in_threads(measure_many) == []

    def test_token_bucket_rate_updates_and_acquires(
        self, frequent_thread_switches: None
    ):
        bucket = TokenBucket(fill_rate=100000.0)

        def update_and_acquire() -> None:
            bucket.update_rate(100000.0)
            for _ in range(500):
                bucket.acquire(1)
                assert bucket.current_capacity >= 0

        assert self._run_in_threads(update_and_acquire) == []

    def test_token_bucket_hands_out_each_token_once(
        self, frequent_thread_switches: None
    ):
        acquires_per_thread = 500
        # Exactly enough tokens for every acquire, so no thread has to wait
        bucket = TokenBucket(curr_capacity=self._THREADS * acquires_per_thread)

        def spend() -> None:
            for _ in range(acquires_per_thread):
                bucket.acquire(1)

        assert self._run_in_threads(spend) == []
        # A lost update to the count would leave tokens behind
        assert bucket.current_capacity < 1


class TestRateLimiter:
    @pytest.mark.parametrize(
        "rate_limiter_enabled, current_bucket_capacity, expected_capacity_after",
        [
            (True, 2.0, 1.0),
            (False, 1.0, 1.0),
        ],
    )
    def test_token_consumption_before_request_scenarios(
        self,
        rate_limiter_enabled: bool,
        current_bucket_capacity: float,
        expected_capacity_after: float,
    ):
        token_bucket = TokenBucket(curr_capacity=current_bucket_capacity)
        limiter = ClientRateLimiter(
            token_bucket=token_bucket,
            cubic_calculator=CubicCalculator(starting_max_rate=1.0, start_time=0.0),
            rate_tracker=RequestRateTracker(),
            rate_limiter_enabled=rate_limiter_enabled,
        )
        limiter.before_sending_request()
        assert token_bucket.current_capacity == expected_capacity_after

    @pytest.mark.parametrize(
        "throttling_error, rate_limiter_enabled, measured_rate, expected_fill_rate",
        [
            (True, False, 5.0, 3.5),
            (True, True, 5.0, 0.5),
            (False, True, 5.0, 7.83),
            (False, False, 5.0, 7.83),
        ],
    )
    def test_token_consumption_after_response_scenarios(
        self,
        throttling_error: bool,
        rate_limiter_enabled: bool,
        measured_rate: float,
        expected_fill_rate: float,
    ):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3]
            token_bucket = TokenBucket()
            limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=CubicCalculator(
                    starting_max_rate=10.0, start_time=0.0
                ),
                rate_tracker=RequestRateTracker(),
                rate_limiter_enabled=rate_limiter_enabled,
            )
            with patch.object(
                limiter._rate_tracker,  # type: ignore[reportPrivateUsage]
                "measure_rate",
                return_value=measured_rate,
            ):
                limiter.after_receiving_response(throttling_error=throttling_error)
        assert round(token_bucket.fill_rate, 2) == expected_fill_rate

    def test_throttling_response_enables_rate_limiter(self):
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4]
            limiter = ClientRateLimiter(
                token_bucket=TokenBucket(),
                cubic_calculator=CubicCalculator(
                    starting_max_rate=10.0, start_time=0.0
                ),
                rate_tracker=RequestRateTracker(),
                rate_limiter_enabled=False,
            )
            limiter.after_receiving_response(throttling_error=True)
        assert limiter.rate_limit_enabled is True

    def test_calculated_rate_is_capped_at_2x_measured_rate(self):
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
                limiter.after_receiving_response(throttling_error=False)
                # Capped at 2x measured rate: 2 * 5.0 = 10.0
                mock_set_rate.assert_called_once_with(10.0)

    def test_new_rate_is_set_while_holding_the_lock(self):
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
        limiter.after_receiving_response(throttling_error=True)
        limiter.after_receiving_response(throttling_error=False)
        assert lock_held == [True, True]


class TestAdaptiveRetryStrategy:
    def test_initialization_with_default_rate_limiter(self):
        strategy = AdaptiveRetryStrategy()
        assert isinstance(strategy.rate_limiter, ClientRateLimiter)
        assert strategy.rate_limiter.rate_limit_enabled is False

    def test_initialization_with_custom_rate_limiter(self):
        custom_limiter = ClientRateLimiter(
            token_bucket=TokenBucket(),
            cubic_calculator=CubicCalculator(starting_max_rate=5.0, start_time=0.0),
            rate_tracker=RequestRateTracker(),
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

    def test_resolver_creates_adaptive_strategy(self):
        resolver = RetryStrategyResolver()
        strategy = resolver.resolve_retry_strategy(
            retry_strategy=RetryStrategyOptions(retry_mode="adaptive")
        )
        assert isinstance(strategy, AdaptiveRetryStrategy)
        assert strategy.max_attempts == 3

    @pytest.mark.parametrize("max_attempts", [2, 3, 10])
    def test_adaptive_retry_strategy(self, max_attempts: int) -> None:
        strategy = AdaptiveRetryStrategy(max_attempts=max_attempts)
        error = CallError(is_retry_safe=True)
        token = strategy.acquire_initial_retry_token()
        for _ in range(max_attempts - 1):
            token = strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )
        with pytest.raises(RetryError):
            strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)

    def test_deepcopy_returns_same_strategy(self) -> None:
        strategy = AdaptiveRetryStrategy()
        copied = deepcopy(strategy)
        assert copied is strategy
        assert copied.rate_limiter is strategy.rate_limiter


class TestRequestPipelineRateLimiting:
    def _non_retryable_call(self, strategy: AdaptiveRetryStrategy) -> Any:
        # A call that skips the retry loop
        call = MagicMock()
        call.retryable.return_value = False
        call.retry_strategy = strategy
        return call

    def _adaptive_strategy_with_mocked_limiter(
        self,
    ) -> tuple[AdaptiveRetryStrategy, ClientRateLimiter]:
        limiter = ClientRateLimiter(
            token_bucket=TokenBucket(),
            cubic_calculator=CubicCalculator(),
            rate_tracker=RequestRateTracker(),
            rate_limiter_enabled=True,
        )
        limiter.before_sending_request = MagicMock()  # type: ignore[method-assign]
        limiter.after_receiving_response = MagicMock()  # type: ignore[method-assign]
        return AdaptiveRetryStrategy(rate_limiter=limiter), limiter

    def test_non_retryable_call_applies_rate_limiting_on_success(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        handle_attempt = MagicMock(
            return_value=SimpleNamespace(transport_response=MagicMock(), response="ok")
        )
        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            pipeline._retry(self._non_retryable_call(strategy), MagicMock())  # type: ignore[reportPrivateUsage]

        handle_attempt.assert_called_once()
        limiter.before_sending_request.assert_called_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_called_once_with(throttling_error=False)  # type: ignore[attr-defined]

    def test_non_retryable_call_reports_throttle_without_retrying(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        error = CallError(is_retry_safe=True, is_throttling_error=True)
        handle_attempt = MagicMock(
            return_value=SimpleNamespace(transport_response=MagicMock(), response=error)
        )
        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            output_context = pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy), MagicMock()
            )

        # Sent once and returned as-is, even though the error is retry-safe
        handle_attempt.assert_called_once()
        assert output_context.response is error
        limiter.before_sending_request.assert_called_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_called_once_with(True)  # type: ignore[attr-defined]

    def test_failure_without_response_does_not_update_rate_limiter(self):
        strategy, limiter = self._adaptive_strategy_with_mocked_limiter()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        # Fails before sending, e.g. endpoint resolution or signing, so no response
        error = CallError(message="Unable to resolve endpoint", is_retry_safe=False)
        handle_attempt = MagicMock(
            return_value=SimpleNamespace(transport_response=None, response=error)
        )
        with patch.object(pipeline, "_handle_attempt", handle_attempt):
            output_context = pipeline._retry(  # type: ignore[reportPrivateUsage]
                self._non_retryable_call(strategy), MagicMock()
            )

        assert output_context.response is error
        limiter.before_sending_request.assert_called_once()  # type: ignore[attr-defined]
        limiter.after_receiving_response.assert_not_called()  # type: ignore[attr-defined]
