# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from asyncio import gather, sleep
from unittest.mock import patch

import pytest
from smithy_core.exceptions import CallError, ClientTimeoutError, RetryError
from smithy_core.interfaces import retries as retries_interface
from smithy_core.retries import (
    AdaptiveRetryStrategy,
    ClientRateLimiter,
    CubicCalculator,
    ExponentialBackoffJitterType,
    ExponentialRetryBackoffStrategy,
    RequestRateTracker,
    StandardRetryQuota,
    StandardRetryStrategy,
    TokenBucket,
)


# TODO: Refactor this to use a smithy-testing generated client
async def retry_operation(
    strategy: retries_interface.RetryStrategy,
    responses: list[int | Exception],
) -> tuple[str, int]:
    token = strategy.acquire_initial_retry_token()
    response_iter = iter(responses)

    while True:
        if token.retry_delay:
            await sleep(token.retry_delay)

        response = next(response_iter)
        attempt = token.retry_count + 1

        # Success case
        if response == 200:
            strategy.record_success(token=token)
            return "success", attempt

        # Error case - either status code or exception
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


async def test_standard_retry_eventually_succeeds():
    quota = StandardRetryQuota(initial_capacity=500)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    result, attempts = await retry_operation(strategy, [500, 500, 200])

    assert result == "success"
    assert attempts == 3
    assert quota.available_capacity == 495


async def test_standard_retry_fails_due_to_max_attempts():
    quota = StandardRetryQuota(initial_capacity=500)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    with pytest.raises(CallError, match="502"):
        await retry_operation(strategy, [502, 502, 502])

    assert quota.available_capacity == 490


async def test_retry_quota_exhausted_after_single_retry():
    quota = StandardRetryQuota(initial_capacity=5)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    with pytest.raises(CallError, match="502"):
        await retry_operation(strategy, [500, 502])

    assert quota.available_capacity == 0


async def test_retry_quota_prevents_retries_when_quota_zero():
    quota = StandardRetryQuota(initial_capacity=0)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    with pytest.raises(CallError, match="500"):
        await retry_operation(strategy, [500])

    assert quota.available_capacity == 0


async def test_retry_quota_stops_retries_when_exhausted():
    quota = StandardRetryQuota(initial_capacity=10)
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=quota)

    with pytest.raises(CallError, match="503"):
        await retry_operation(strategy, [500, 502, 503])

    assert quota.available_capacity == 0


async def test_retry_quota_recovers_after_successful_responses():
    quota = StandardRetryQuota(initial_capacity=15)
    strategy = StandardRetryStrategy(max_attempts=5, retry_quota=quota)

    # First operation: 2 retries then success
    await retry_operation(strategy, [500, 502, 200])
    assert quota.available_capacity == 10

    # Second operation: 1 retry then success
    await retry_operation(strategy, [500, 200])
    assert quota.available_capacity == 10


async def test_retry_quota_shared_across_concurrent_operations():
    quota = StandardRetryQuota(initial_capacity=500)
    backoff = ExponentialRetryBackoffStrategy(
        backoff_scale_value=1,
        max_backoff=10,
        jitter_type=ExponentialBackoffJitterType.FULL,
    )
    strategy = StandardRetryStrategy(
        max_attempts=5,
        retry_quota=quota,
        backoff_strategy=backoff,
    )

    result1, result2 = await gather(
        retry_operation(strategy, [500, 500, 200]),
        retry_operation(strategy, [500, 200]),
    )

    assert result1 == ("success", 3)
    assert result2 == ("success", 2)
    assert quota.available_capacity == 495


async def test_retry_quota_handles_timeout_errors():
    quota = StandardRetryQuota(initial_capacity=500)
    strategy = StandardRetryStrategy(max_attempts=3, retry_quota=quota)

    timeout1 = ClientTimeoutError()
    timeout2 = ClientTimeoutError()

    result, attempts = await retry_operation(strategy, [timeout1, timeout2, 200])

    assert result == "success"
    assert attempts == 3
    assert quota.available_capacity == 490


class TestAdaptiveRetryStrategy:
    async def retry_operation_with_rate_limiting(
        self,
        strategy: AdaptiveRetryStrategy,
        responses: list[int | Exception],
    ) -> tuple[str, int]:
        token = strategy.acquire_initial_retry_token()
        response_iter = iter(responses)

        while True:
            if token.retry_delay:
                await sleep(token.retry_delay)

            try:
                # Rate limiting step - acquire token from bucket (can raise TimeoutError)
                await strategy.acquire_from_token_bucket()
            except TimeoutError as timeout_error:
                error = CallError(
                    fault="client",
                    message=str(timeout_error),
                    is_retry_safe=True,  # Make it retryable
                )
                # Timeout should be treated as a retryable error
                try:
                    token = strategy.refresh_retry_token_for_retry(
                        token_to_renew=token, error=error
                    )
                    continue  # Retry without consuming a response
                except RetryError:
                    raise timeout_error

            response = next(response_iter)
            attempt = token.retry_count + 1

            # Success case
            if response == 200:
                await strategy.rate_limiter.after_receiving_response(
                    throttling_error=False
                )
                strategy.record_success(token=token)
                return "success", attempt

            # Error case - we got a response (even if it's an error)
            if isinstance(response, Exception):
                error = response
            else:
                error = CallError(
                    fault="server" if response >= 500 else "client",
                    message=f"HTTP {response}",
                    is_retry_safe=response >= 500 or response == 429,
                    is_throttling_error=response == 429,
                )
            is_throttling = strategy.is_throttling_error(error)
            # Update rate limiter after error response
            await strategy.rate_limiter.after_receiving_response(
                throttling_error=is_throttling
            )

            try:
                token = strategy.refresh_retry_token_for_retry(
                    token_to_renew=token, error=error
                )
            except RetryError:
                raise error

    async def test_adaptive_retry_eventually_succeeds(self):
        quota = StandardRetryQuota(initial_capacity=500)
        strategy = AdaptiveRetryStrategy(max_attempts=3, retry_quota=quota)

        result, attempts = await retry_operation(strategy, [500, 500, 200])

        assert result == "success"
        assert attempts == 3
        assert quota.available_capacity == 495

    async def test_adaptive_retry_fails_due_to_max_attempts(self):
        quota = StandardRetryQuota(initial_capacity=500)
        strategy = AdaptiveRetryStrategy(max_attempts=3, retry_quota=quota)

        with pytest.raises(CallError, match="502"):
            await retry_operation(strategy, [502, 502, 502])

        assert quota.available_capacity == 490

    async def test_adaptive_retry_timeout_counts_as_attempt(self):
        # Test that token acquisition timeout counts as a retry attempt and continues retrying
        quota = StandardRetryQuota(initial_capacity=500)

        time_counter = [0.0]

        def mock_monotonic():
            # Mock time progression to trigger timeout on first attempt:
            # Time values: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 31, 31.1...]
            # First attempt: start_time=0.6, timeout_check=31.0
            # Elapsed time: 31.0 - 0.6 = 30.4 seconds > 30s timeout threshold
            # Result: TimeoutError raised, counted as attempt 1, then retries continue

            current = time_counter[0]
            # Jump to timeout on specific call (e.g., 8th call)
            if time_counter[0] == 0.6:  # After initial setup
                time_counter[0] = 31.0  # Jump to timeout
            else:
                time_counter[0] += 0.1
            return current

        with (
            patch("time.monotonic", side_effect=mock_monotonic),
            patch("asyncio.sleep"),
        ):  # mock asyncio.sleep while acquiring token
            token_bucket = TokenBucket()
            rate_limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=CubicCalculator(),
                rate_tracker=RequestRateTracker(),
                rate_limiter_enabled=True,
            )

            # Drain the initial token
            await rate_limiter.before_sending_request()

            strategy = AdaptiveRetryStrategy(
                max_attempts=3, retry_quota=quota, rate_limiter=rate_limiter
            )

            result, attempts = await self.retry_operation_with_rate_limiting(
                strategy, [500, 200]
            )

            assert result == "success"
            assert attempts == 3
            assert quota.available_capacity == 495

    async def test_adaptive_retry_throttle_enables_rate_limiting(self):
        # Test that a 429 throttle response enables rate limiting and subsequent
        # requests go through the token bucket
        time_counter = [0.0]

        def mock_monotonic():
            current = time_counter[0]
            time_counter[0] += 0.1
            return current

        with (
            patch("time.monotonic", side_effect=mock_monotonic),
            patch("asyncio.sleep"),
        ):
            token_bucket = TokenBucket()
            tracker = RequestRateTracker()
            calculator = CubicCalculator(starting_max_rate=10.0, start_time=0.0)
            rate_limiter = ClientRateLimiter(
                token_bucket=token_bucket,
                cubic_calculator=calculator,
                rate_tracker=tracker,
                rate_limiter_enabled=False,
            )

            strategy = AdaptiveRetryStrategy(max_attempts=4, rate_limiter=rate_limiter)

            assert rate_limiter.rate_limit_enabled is False

            # First request gets 429 (throttled), second gets 500 (server error),
            # third succeeds.
            result, attempts = await self.retry_operation_with_rate_limiting(
                strategy, [429, 500, 200]
            )

            assert result == "success"
            assert attempts == 3
            # Rate limiting should now be enabled after the 429
            assert rate_limiter.rate_limit_enabled is True
