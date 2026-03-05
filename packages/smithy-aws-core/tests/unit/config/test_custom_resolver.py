# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from smithy_aws_core.config.custom_resolvers import resolve_retry_strategy
from smithy_core.config.resolver import ConfigResolver
from smithy_core.retries import RetryStrategyOptions


class StubSource:
    """A simple ConfigSource implementation for testing."""

    def __init__(self, source_name: str, data: dict[str, Any] | None = None) -> None:
        self._name = source_name
        self._data = data or {}

    @property
    def name(self) -> str:
        return self._name

    def get(self, key: str) -> Any | None:
        return self._data.get(key)


class TestResolveCustomResolverRetryStrategy:
    """Test suite for complex configuration resolution"""

    def test_resolves_from_both_values(self) -> None:
        # When both retry mode and max attempts are set
        # It should use source names for both values
        source = StubSource(
            "environment", {"retry_mode": "standard", "max_attempts": "3"}
        )
        resolver = ConfigResolver(sources=[source])

        result, source_name = resolve_retry_strategy(resolver)

        assert isinstance(result, RetryStrategyOptions)
        assert result.retry_mode == "standard"
        assert result.max_attempts == 3
        assert source_name == "retry_mode=environment, max_attempts=environment"

    def test_tracks_different_sources_for_each_component(self) -> None:
        source1 = StubSource("environment", {"retry_mode": "standard"})
        source2 = StubSource("config_file", {"max_attempts": "5"})
        resolver = ConfigResolver(sources=[source1, source2])

        result, source_name = resolve_retry_strategy(resolver)

        assert isinstance(result, RetryStrategyOptions)
        assert result.retry_mode == "standard"
        assert result.max_attempts == 5
        assert source_name == "retry_mode=environment, max_attempts=config_file"

    def test_converts_max_attempts_string_to_int(self) -> None:
        source = StubSource(
            "environment", {"max_attempts": "10", "retry_mode": "standard"}
        )
        resolver = ConfigResolver(sources=[source])

        result, _ = resolve_retry_strategy(resolver)

        assert isinstance(result, RetryStrategyOptions)
        assert result.max_attempts == 10
        assert isinstance(result.max_attempts, int)

    def test_returns_strategy_when_only_retry_mode_set(self) -> None:
        source = StubSource("environment", {"retry_mode": "standard"})
        resolver = ConfigResolver(sources=[source])

        result, source_name = resolve_retry_strategy(resolver)

        assert isinstance(result, RetryStrategyOptions)
        assert result.retry_mode == "standard"
        assert result.max_attempts is None
        assert source_name == "retry_mode=environment, max_attempts=default"

    def test_returns_strategy_when_only_max_attempts_set(self) -> None:
        source = StubSource("environment", {"max_attempts": "5"})
        resolver = ConfigResolver(sources=[source])

        result, source_name = resolve_retry_strategy(resolver)

        assert isinstance(result, RetryStrategyOptions)
        assert result.max_attempts == 5
        assert result.retry_mode == "standard"
        assert source_name == "retry_mode=default, max_attempts=environment"

    def test_returns_none_when_both_values_missing(self) -> None:
        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])

        result, source_name = resolve_retry_strategy(resolver)

        assert result is None
        assert source_name is None
