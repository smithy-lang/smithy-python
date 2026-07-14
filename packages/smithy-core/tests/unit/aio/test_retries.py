#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.aio.retries import (
    RetryStrategyOptions,
    RetryStrategyResolver,
    SimpleRetryStrategy,
    StandardRetryStrategy,
)
from smithy_core.exceptions import CallError, RetryError
from smithy_core.retries import (
    LONG_POLLING,
    ExponentialRetryBackoffStrategy,
    StandardRetryQuota,
)
from smithy_core.retries import (
    ExponentialBackoffJitterType as EBJT,
)
from smithy_core.types import TypedProperties


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


async def test_simple_retry_does_not_retry_when_safety_unknown() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(is_retry_safe=None)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


async def test_simple_retry_does_not_retry_unsafe() -> None:
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=5),
        max_attempts=2,
    )
    error = CallError(fault="client", is_retry_safe=False)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


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


@pytest.mark.parametrize(
    "error",
    [
        Exception(),
        CallError(is_retry_safe=None),
        CallError(fault="client", is_retry_safe=False),
    ],
    ids=[
        "unclassified_error",
        "safety_unknown_error",
        "unsafe_error",
    ],
)
async def test_standard_retry_does_not_retry(error: Exception | CallError) -> None:
    strategy = StandardRetryStrategy()
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError):
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)


async def test_standard_retry_after_within_bounds_is_honored() -> None:
    strategy = StandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        )
    )
    error = CallError(is_retry_safe=True, retry_after=3.0)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 3.0


async def test_standard_retry_after_floored_to_backoff() -> None:
    strategy = StandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        )
    )
    error = CallError(is_retry_safe=True, retry_after=0.5)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 1.0


async def test_standard_retry_after_capped_at_backoff_plus_max() -> None:
    strategy = StandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        )
    )
    error = CallError(is_retry_safe=True, retry_after=10.0)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 6.0


async def test_standard_non_throttling_uses_default_backoff_scale() -> None:
    strategy = StandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=0.05,
            jitter_type=EBJT.NONE,
        )
    )
    error = CallError(is_retry_safe=True, is_throttling_error=False)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == pytest.approx(0.05)  # type: ignore


async def test_standard_throttling_uses_throttling_backoff_scale() -> None:
    strategy = StandardRetryStrategy(
        throttling_backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1,
            jitter_type=EBJT.NONE,
        )
    )
    error = CallError(is_retry_safe=True, is_throttling_error=True)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == pytest.approx(1.0)  # type: ignore


async def test_dynamodb_profile_uses_25ms_scale_and_4_attempts() -> None:
    strategy = StandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=0.025, jitter_type=EBJT.NONE
        ),
        max_attempts=4,
    )
    assert strategy.max_attempts == 4

    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == pytest.approx(0.025)  # type: ignore
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == pytest.approx(0.05)  # type: ignore


def _long_polling_context() -> TypedProperties:
    context = TypedProperties()
    context[LONG_POLLING] = True
    return context


async def test_long_polling_backs_off_when_quota_exhausted() -> None:
    strategy = StandardRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=0.05, jitter_type=EBJT.NONE
        ),
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    context = _long_polling_context()
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token(context=context)
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error, context=context
        )
    assert exc_info.value.retry_after == pytest.approx(0.05)  # type: ignore


async def test_long_polling_throttling_backs_off_with_throttling_scale() -> None:
    strategy = StandardRetryStrategy(
        throttling_backoff_strategy=ExponentialRetryBackoffStrategy(
            backoff_scale_value=1, jitter_type=EBJT.NONE
        ),
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    context = _long_polling_context()
    error = CallError(is_retry_safe=True, is_throttling_error=True)
    token = await strategy.acquire_initial_retry_token(context=context)
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error, context=context
        )
    assert exc_info.value.retry_after == pytest.approx(1.0)  # type: ignore


async def test_long_polling_no_backoff_when_max_attempts_reached() -> None:
    strategy = StandardRetryStrategy(
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=1,
    )
    context = _long_polling_context()
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token(context=context)
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error, context=context
        )
    assert exc_info.value.retry_after is None


async def test_long_polling_no_backoff_for_non_retryable_error() -> None:
    strategy = StandardRetryStrategy(
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    context = _long_polling_context()
    error = CallError(fault="client", is_retry_safe=False)
    token = await strategy.acquire_initial_retry_token(context=context)
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(
            token_to_renew=token, error=error, context=context
        )
    assert exc_info.value.retry_after is None


async def test_non_long_polling_does_not_back_off_when_quota_exhausted() -> None:
    strategy = StandardRetryStrategy(
        retry_quota=StandardRetryQuota(initial_capacity=0),
        max_attempts=5,
    )
    error = CallError(is_retry_safe=True)
    token = await strategy.acquire_initial_retry_token()
    with pytest.raises(RetryError) as exc_info:
        await strategy.refresh_retry_token_for_retry(token_to_renew=token, error=error)
    assert exc_info.value.retry_after is None


async def test_standard_retry_invalid_max_attempts() -> None:
    with pytest.raises(ValueError):
        StandardRetryStrategy(max_attempts=-1)


async def test_retry_strategy_resolver_none_returns_default() -> None:
    resolver = RetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 3


async def test_retry_strategy_resolver_creates_different_strategies() -> None:
    resolver = RetryStrategyResolver()

    options1 = RetryStrategyOptions(max_attempts=3)
    options2 = RetryStrategyOptions(max_attempts=5)

    strategy1 = await resolver.resolve_retry_strategy(retry_strategy=options1)
    strategy2 = await resolver.resolve_retry_strategy(retry_strategy=options2)

    assert strategy1.max_attempts == 3
    assert strategy2.max_attempts == 5
    assert strategy1 is not strategy2


async def test_retry_strategy_resolver_caches_strategies() -> None:
    resolver = RetryStrategyResolver()

    strategy1 = await resolver.resolve_retry_strategy(retry_strategy=None)
    strategy2 = await resolver.resolve_retry_strategy(retry_strategy=None)
    options = RetryStrategyOptions(max_attempts=5)
    strategy3 = await resolver.resolve_retry_strategy(retry_strategy=options)
    strategy4 = await resolver.resolve_retry_strategy(retry_strategy=options)

    assert strategy1 is strategy2
    assert strategy3 is strategy4
    assert strategy1 is not strategy3


async def test_retry_strategy_resolver_returns_existing_strategy() -> None:
    resolver = RetryStrategyResolver()
    provided_strategy = SimpleRetryStrategy(max_attempts=7)

    strategy = await resolver.resolve_retry_strategy(retry_strategy=provided_strategy)

    assert strategy is provided_strategy
    assert strategy.max_attempts == 7


async def test_retry_strategy_resolver_rejects_invalid_type() -> None:
    resolver = RetryStrategyResolver()

    with pytest.raises(
        TypeError,
        match="retry_strategy must be RetryStrategy, RetryStrategyOptions, or None",
    ):
        await resolver.resolve_retry_strategy(retry_strategy="invalid")  # type: ignore


async def test_resolver_service_defaults_applied_when_customer_unset() -> None:
    resolver = RetryStrategyResolver(
        default_max_attempts=4, default_backoff_scale=0.025
    )

    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 4
    delay = strategy.backoff_strategy.compute_next_backoff_delay(1)
    assert 0 <= delay <= 0.025


async def test_resolver_customer_max_attempts_overrides_default_keeps_backoff() -> None:
    resolver = RetryStrategyResolver(
        default_max_attempts=4, default_backoff_scale=0.025
    )

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=RetryStrategyOptions(max_attempts=10)
    )

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 10
    delay = strategy.backoff_strategy.compute_next_backoff_delay(1)
    assert 0 <= delay <= 0.025


async def test_resolver_empty_options_still_get_service_defaults() -> None:
    resolver = RetryStrategyResolver(
        default_max_attempts=4, default_backoff_scale=0.025
    )

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=RetryStrategyOptions()
    )

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 4
    delay = strategy.backoff_strategy.compute_next_backoff_delay(1)
    assert 0 <= delay <= 0.025


async def test_resolver_no_service_defaults_uses_strategy_defaults() -> None:
    resolver = RetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 3
    delay = strategy.backoff_strategy.compute_next_backoff_delay(1)
    assert 0 <= delay <= 0.05


async def test_resolver_explicit_strategy_ignores_service_defaults() -> None:
    resolver = RetryStrategyResolver(
        default_max_attempts=4, default_backoff_scale=0.025
    )
    provided = StandardRetryStrategy(max_attempts=7)

    strategy = await resolver.resolve_retry_strategy(retry_strategy=provided)

    assert strategy is provided
    assert strategy.max_attempts == 7
