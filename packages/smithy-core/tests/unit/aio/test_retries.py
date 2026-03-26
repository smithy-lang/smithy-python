#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import asyncio

import pytest
from smithy_core.aio.retries import (
    SimpleRetryStrategy,
    TokenBucket,
    TokenBucketRetryStrategy,
)
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import ExponentialRetryBackoffStrategy


class TestSimpleRetryStrategy:
    @pytest.mark.parametrize("max_attempts", [2, 3, 10])
    async def test_retries_until_max_attempts(self, max_attempts: int) -> None:
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
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_does_not_retry_unclassified(self) -> None:
        strategy = SimpleRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
            max_attempts=2,
        )
        token = await strategy.acquire_initial_retry_token()
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=Exception()
            )

    async def test_does_not_retry_when_safety_unknown(self) -> None:
        strategy = SimpleRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
            max_attempts=2,
        )
        error = CallError(is_retry_safe=None)
        token = await strategy.acquire_initial_retry_token()
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_does_not_retry_unsafe(self) -> None:
        strategy = SimpleRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
            max_attempts=2,
        )
        error = CallError(fault="client", is_retry_safe=False)
        token = await strategy.acquire_initial_retry_token()
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )


class TestTokenBucket:
    async def test_drain(self) -> None:
        bucket = TokenBucket(max_capacity=10)
        assert await bucket.drain(7) is True
        assert await bucket.drain(3) is True
        assert await bucket.drain(1) is False

    async def test_drain_rejects_zero(self) -> None:
        bucket = TokenBucket()
        with pytest.raises(ValueError):
            await bucket.drain(0)

    async def test_drain_rejects_negative(self) -> None:
        bucket = TokenBucket()
        with pytest.raises(ValueError):
            await bucket.drain(-1)

    async def test_drain_rejects_over_capacity(self) -> None:
        bucket = TokenBucket(max_capacity=10)
        with pytest.raises(ValueError):
            await bucket.drain(11)

    async def test_fill_adds_tokens(self) -> None:
        bucket = TokenBucket(max_capacity=10)
        await bucket.drain(10)
        await bucket.fill(5)
        assert await bucket.drain(5) is True
        assert await bucket.drain(1) is False

    async def test_fill_caps_at_max_capacity(self) -> None:
        bucket = TokenBucket(max_capacity=10)
        assert await bucket.drain(1) is True
        await bucket.fill(100)
        assert await bucket.drain(10) is True
        assert await bucket.drain(1) is False

    async def test_fill_rejects_zero(self) -> None:
        bucket = TokenBucket()
        with pytest.raises(ValueError):
            await bucket.fill(0)

    async def test_fill_rejects_negative(self) -> None:
        bucket = TokenBucket()
        with pytest.raises(ValueError):
            await bucket.fill(-1)

    async def test_drain_wait_on_empty_blocks_until_filled(self) -> None:
        bucket = TokenBucket(max_capacity=10)
        await bucket.drain(10)

        result: bool | None = None

        async def drainer() -> None:
            nonlocal result
            result = await bucket.drain(5, wait_on_empty=True)

        task = asyncio.create_task(drainer())
        await asyncio.sleep(0.05)
        assert result is None

        await bucket.fill(5)
        await task
        assert result is True

    async def test_drain_wait_on_empty_returns_immediately_when_available(
        self,
    ) -> None:
        bucket = TokenBucket(max_capacity=10)
        assert await bucket.drain(5, wait_on_empty=True) is True


class TestTokenBucketRetryStrategy:
    async def test_acquire_initial_token(self) -> None:
        strategy = TokenBucketRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
            max_attempts=3,
        )
        token = await strategy.acquire_initial_retry_token()
        assert token.retry_count == 0
        assert token.retry_delay == 0

    async def test_acquire_initial_token_with_empty_bucket(self) -> None:
        strategy = TokenBucketRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
            max_attempts=3,
            token_bucket_capacity=10,
        )
        await strategy._token_bucket.drain(10)
        token = await strategy.acquire_initial_retry_token()
        assert token.retry_count == 0
        assert token.retry_delay == 0

    @pytest.mark.parametrize("max_attempts", [2, 3, 5])
    async def test_retries_until_max_attempts(self, max_attempts: int) -> None:
        strategy = TokenBucketRetryStrategy(
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
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_does_not_retry_unclassified_error(self) -> None:
        strategy = TokenBucketRetryStrategy(max_attempts=5)
        token = await strategy.acquire_initial_retry_token()
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=Exception()
            )

    async def test_does_not_retry_when_safety_unknown(self) -> None:
        strategy = TokenBucketRetryStrategy(max_attempts=5)
        error = CallError(is_retry_safe=None)
        token = await strategy.acquire_initial_retry_token()
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_does_not_retry_unsafe_error(self) -> None:
        strategy = TokenBucketRetryStrategy(max_attempts=5)
        error = CallError(fault="client", is_retry_safe=False)
        token = await strategy.acquire_initial_retry_token()
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_retry_drains_bucket(self) -> None:
        strategy = TokenBucketRetryStrategy(
            token_bucket_capacity=30,
            retry_cost=30,
        )
        error = CallError(is_retry_safe=True)
        token = await strategy.acquire_initial_retry_token()

        # Drain the bucket to 0
        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )

        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_throttling_error_uses_throttling_cost(self) -> None:
        strategy = TokenBucketRetryStrategy(
            max_attempts=100,
            token_bucket_capacity=20,
            retry_cost=20,
            throttling_retry_cost=10,
        )
        error = CallError(is_retry_safe=True, is_throttling_error=True)
        token = await strategy.acquire_initial_retry_token()
        for _ in range(2):
            token = await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )
        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

    async def test_record_success_refills_bucket(self) -> None:
        strategy = TokenBucketRetryStrategy(
            token_bucket_capacity=10,
            retry_cost=10,
            success_increment=10,
        )
        error = CallError(is_retry_safe=True)
        token = await strategy.acquire_initial_retry_token()

        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )

        with pytest.raises(RetryError):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )

        await strategy.record_success(token=token)

        token = await strategy.acquire_initial_retry_token()
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)

    async def test_max_attempts_checked_before_bucket(self) -> None:
        strategy = TokenBucketRetryStrategy(
            token_bucket_capacity=500,
            max_attempts=2,
        )
        error = CallError(is_retry_safe=True)
        token = await strategy.acquire_initial_retry_token()
        token = await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error
        )
        with pytest.raises(RetryError, match="attempts"):
            await strategy.refresh_retry_token_for_retry(
                token_to_renew=token, error=error
            )
