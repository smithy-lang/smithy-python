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
    ExponentialRetryBackoffStrategy,
)


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


async def test_standard_retry_after_overrides_backoff() -> None:
    strategy = StandardRetryStrategy()
    error = CallError(is_retry_safe=True, retry_after=5.5)
    token = await strategy.acquire_initial_retry_token()
    token = await strategy.refresh_retry_token_for_retry(
        token_to_renew=token, error=error
    )
    assert token.retry_delay == 5.5


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


async def test_retry_strategy_resolver_uses_max_attempts_fallback() -> None:
    resolver = RetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=None, max_attempts=9
    )

    assert isinstance(strategy, StandardRetryStrategy)
    assert strategy.max_attempts == 9


async def test_retry_strategy_resolver_uses_retry_mode_fallback() -> None:
    resolver = RetryStrategyResolver()

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=None, retry_mode="simple", max_attempts=4
    )

    assert isinstance(strategy, SimpleRetryStrategy)
    assert strategy.max_attempts == 4


async def test_retry_strategy_resolver_fallback_defaults_when_unset() -> None:
    """Omitting both fallbacks must match the prior no-argument behavior."""
    resolver = RetryStrategyResolver()

    explicit = await resolver.resolve_retry_strategy(
        retry_strategy=None, retry_mode=None, max_attempts=None
    )
    baseline = await resolver.resolve_retry_strategy(retry_strategy=None)

    assert explicit is baseline
    assert isinstance(explicit, StandardRetryStrategy)
    assert explicit.max_attempts == 3


async def test_explicit_retry_strategy_options_beat_fallbacks() -> None:
    resolver = RetryStrategyResolver()
    retry_strategy = RetryStrategyOptions(max_attempts=2)

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=retry_strategy, max_attempts=9
    )

    assert strategy.max_attempts == 2


async def test_explicit_retry_strategy_instance_beats_fallbacks() -> None:
    resolver = RetryStrategyResolver()
    provided = SimpleRetryStrategy(max_attempts=7)

    strategy = await resolver.resolve_retry_strategy(
        retry_strategy=provided, retry_mode="standard", max_attempts=9
    )

    assert strategy is provided
    assert strategy.max_attempts == 7
