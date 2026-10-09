# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from asyncio import gather, sleep, wait_for
from collections.abc import Coroutine
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smithy_core.aio.client import RequestPipeline
from smithy_core.exceptions import CallError, ClientTimeoutError, RetryError
from smithy_core.interceptors import RequestContext
from smithy_core.interfaces import retries as retries_interface
from smithy_core.retries import (
    AdaptiveRetryStrategy,
    ExponentialBackoffJitterType,
    ExponentialRetryBackoffStrategy,
    StandardRetryQuota,
    StandardRetryStrategy,
)
from smithy_core.types import TypedProperties


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


class FakeClock:
    """Simulated time for the adaptive retry pipeline.

    Replaces the clock read by the rate limiter, the retry backoff sleep, and the
    token bucket wait, so simulated seconds pass instantly and deterministically.
    """

    # A real event loop always advances time by at least this much per wait
    _MIN_WAIT = 1e-6

    def __init__(self) -> None:
        self.now = 0.0
        self.backoffs: list[float] = []

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, delay: float) -> None:
        self.backoffs.append(delay)
        self.now += delay

    async def wait_for(self, coro: Coroutine[Any, Any, Any], timeout: float) -> None:  # noqa: ASYNC109
        # Nothing notifies a waiter in a single-client simulation, so every wait
        # times out after the full duration
        coro.close()
        self.now += max(timeout, self._MIN_WAIT)
        raise TimeoutError


class TestAdaptiveRetryPipeline:
    @pytest.fixture
    def clock(self):
        clock = FakeClock()
        with (
            patch(
                "smithy_core.retries.time", SimpleNamespace(monotonic=clock.monotonic)
            ),
            patch("smithy_core.aio.client.sleep", clock.sleep),
            patch("smithy_core.retries.asyncio.wait_for", clock.wait_for),
        ):
            yield clock

    def _call(self, strategy: AdaptiveRetryStrategy) -> Any:
        call = MagicMock()
        call.retryable.return_value = True
        call.retry_strategy = strategy
        call.retry_scope = None
        return call

    def _request_context(self) -> RequestContext[Any, Any]:
        return RequestContext(
            request=MagicMock(),
            transport_request=SimpleNamespace(body=b""),
            properties=TypedProperties(),
        )

    def _response(self, status: int) -> CallError | str:
        if status == 200:
            return "ok"
        return CallError(
            fault="server" if status >= 500 else "client",
            message=f"HTTP {status}",
            is_retry_safe=True,
            is_throttling_error=status == 429,
        )

    @pytest.mark.parametrize(
        "statuses, expected",
        [
            # (rate limiting wait, response status, backoff, terminal)
            (
                [429, 429, 429],
                [
                    (0.0, 429, 0.5, False),
                    (0.0, 429, 1.0, False),
                    (1.0, 429, None, True),
                ],
            ),
            (
                [429, 500, 200],
                [
                    (0.0, 429, 0.5, False),
                    (0.0, 500, 1.0, False),
                    (1.0, 200, None, True),
                ],
            ),
        ],
        ids=["throttled_until_max_attempts", "throttle_then_success"],
    )
    async def test_adaptive_retry_sequence(
        self,
        clock: FakeClock,
        statuses: list[int],
        expected: list[tuple[float, int, float | None, bool]],
    ):
        # Full jitter that always picks the midpoint, so backoff is deterministic
        backoff = ExponentialRetryBackoffStrategy(
            backoff_scale_value=1,
            jitter_type=ExponentialBackoffJitterType.FULL,
            random=lambda: 0.5,
        )
        strategy = AdaptiveRetryStrategy(max_attempts=3, backoff_strategy=backoff)
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        responses = iter(statuses)
        sent: list[tuple[float, int]] = []
        attempt_start = 0.0

        async def handle_attempt(*args: Any) -> SimpleNamespace:
            status = next(responses)
            sent.append((clock.now - attempt_start, status))
            return SimpleNamespace(response=self._response(status))

        original_pre_request = pipeline._handle_pre_request_rate_limiting  # type: ignore[reportPrivateUsage]

        async def pre_request(retry_strategy: Any) -> None:
            nonlocal attempt_start
            attempt_start = clock.now
            await original_pre_request(retry_strategy)

        with (
            patch.object(
                pipeline, "_handle_attempt", AsyncMock(side_effect=handle_attempt)
            ),
            patch.object(pipeline, "_handle_pre_request_rate_limiting", pre_request),
        ):
            try:
                await pipeline._retry(  # type: ignore[reportPrivateUsage]
                    self._call(strategy), self._request_context(), None
                )
            except CallError:
                pass

        assert strategy.rate_limiter.rate_limit_enabled
        backoffs: list[float | None] = [*clock.backoffs, None]
        actual = [
            (round(wait, 6), status, backoffs[i], i == len(sent) - 1)
            for i, (wait, status) in enumerate(sent)
        ]
        assert actual == expected

    async def test_adaptive_retry_send_rate_converges_to_server_limit(
        self, clock: FakeClock
    ):
        # The server lets through 10 requests per second and throttles the rest,
        # while the client attempts 100 requests per second
        server_rps = 10.0
        client_interval = 0.01
        duration = 120.0

        # No retries, so backoff can't slow the client; only rate limiting can
        strategy = AdaptiveRetryStrategy(max_attempts=1)
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        server_tokens = server_rps
        server_last_refill = 0.0
        sent: list[float] = []
        succeeded: list[float] = []

        async def handle_attempt(*args: Any) -> SimpleNamespace:
            nonlocal server_tokens, server_last_refill
            elapsed = clock.now - server_last_refill
            server_tokens = min(server_rps, server_tokens + elapsed * server_rps)
            server_last_refill = clock.now
            sent.append(clock.now)
            if server_tokens >= 1:
                server_tokens -= 1
                succeeded.append(clock.now)
                return SimpleNamespace(response=self._response(200))
            return SimpleNamespace(response=self._response(429))

        with patch.object(
            pipeline, "_handle_attempt", AsyncMock(side_effect=handle_attempt)
        ):
            while clock.now < duration:
                try:
                    await pipeline._retry(  # type: ignore[reportPrivateUsage]
                        self._call(strategy), self._request_context(), None
                    )
                except CallError:
                    pass
                clock.now += client_interval

        # Measure the steady state over the last 30 simulated seconds
        window_start = duration - 30
        send_rate = sum(t >= window_start for t in sent) / 30
        success_rate = sum(t >= window_start for t in succeeded) / 30
        assert send_rate < 15
        # Converging must not over-throttle the client well below the server limit
        assert success_rate > 8

    async def test_input_stream_raises_when_send_token_acquisition_fails(self):
        strategy = AdaptiveRetryStrategy()
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        call = self._call(strategy)
        # Event stream inputs aren't retryable
        call.retryable.return_value = False
        error = TimeoutError("Failed to acquire 1.0 tokens within 30.0s")

        with patch.object(
            strategy, "acquire_from_token_bucket", AsyncMock(side_effect=error)
        ):
            # Bound the wait so a regression fails instead of hanging the suite
            with pytest.raises(TimeoutError, match="Failed to acquire"):
                await wait_for(pipeline.input_stream(call, Any), timeout=1)

    @pytest.mark.parametrize(
        "acquire_results, expected_error",
        [
            # The first attempt can't get a send token, so there's no service error
            ([TimeoutError("Failed to acquire")], TimeoutError),
            # The retry after a throttle can't get a send token
            ([None, TimeoutError("Failed to acquire")], CallError),
        ],
        ids=["first_attempt", "retry"],
    )
    async def test_send_token_timeout_surfaces_last_service_error(
        self, acquire_results: list[Exception | None], expected_error: type[Exception]
    ):
        quota = StandardRetryQuota(initial_capacity=500)
        strategy = AdaptiveRetryStrategy(max_attempts=3, retry_quota=quota)
        pipeline: RequestPipeline[Any, Any] = RequestPipeline(
            protocol=MagicMock(), transport=MagicMock()
        )
        attempt = AsyncMock(return_value=SimpleNamespace(response=self._response(429)))

        with (
            patch.object(pipeline, "_handle_attempt", attempt),
            patch.object(
                strategy,
                "acquire_from_token_bucket",
                AsyncMock(side_effect=acquire_results),
            ),
            patch("smithy_core.aio.client.sleep", AsyncMock()),
        ):
            with pytest.raises(expected_error) as exc_info:
                await pipeline._retry(  # type: ignore[reportPrivateUsage]
                    self._call(strategy), self._request_context(), None
                )

        if expected_error is TimeoutError:
            # Nothing was sent, so no retry quota was spent
            assert quota.available_capacity == 500
        if expected_error is CallError:
            assert exc_info.value.is_throttling_error  # type: ignore[attr-defined]
            assert isinstance(exc_info.value.__cause__, TimeoutError)
