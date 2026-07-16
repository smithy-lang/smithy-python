# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the DynamoDB retry-defaults plugin."""

from dataclasses import dataclass

from smithy_aws_core.plugins import dynamodb_retry_plugin
from smithy_core.aio.interfaces.retries import RetryStrategy
from smithy_core.aio.retries import StandardRetryStrategy
from smithy_core.retries import RetryStrategyOptions


@dataclass
class _FakeConfig:
    retry_strategy: RetryStrategy | RetryStrategyOptions | None = None


def _backoff_at(strategy: StandardRetryStrategy, attempt: int) -> float:
    return strategy.backoff_strategy.compute_next_backoff_delay(attempt)


def test_builds_strategy_with_defaults_when_unset() -> None:
    config = _FakeConfig(retry_strategy=None)
    dynamodb_retry_plugin(config)
    assert isinstance(config.retry_strategy, StandardRetryStrategy)
    assert config.retry_strategy.max_attempts == 4
    assert 0 <= _backoff_at(config.retry_strategy, 1) <= 0.025


def test_builds_strategy_from_empty_options() -> None:
    config = _FakeConfig(retry_strategy=RetryStrategyOptions(retry_mode="standard"))
    dynamodb_retry_plugin(config)
    assert isinstance(config.retry_strategy, StandardRetryStrategy)
    assert config.retry_strategy.max_attempts == 4
    assert 0 <= _backoff_at(config.retry_strategy, 1) <= 0.025


def test_customer_max_attempts_wins() -> None:
    config = _FakeConfig(retry_strategy=RetryStrategyOptions(max_attempts=10))
    dynamodb_retry_plugin(config)
    assert isinstance(config.retry_strategy, StandardRetryStrategy)
    assert config.retry_strategy.max_attempts == 10
    assert 0 <= _backoff_at(config.retry_strategy, 1) <= 0.025


def test_simple_mode_is_left_untouched() -> None:
    options = RetryStrategyOptions(retry_mode="simple")
    config = _FakeConfig(retry_strategy=options)
    dynamodb_retry_plugin(config)
    assert config.retry_strategy is options


def test_full_custom_strategy_is_left_untouched() -> None:
    strategy = StandardRetryStrategy(max_attempts=7)
    config = _FakeConfig(retry_strategy=strategy)
    dynamodb_retry_plugin(config)
    assert config.retry_strategy is strategy
