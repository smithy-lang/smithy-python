# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import pytest
from pytest import MonkeyPatch
from smithy_aws_core.config.custom_resolvers import resolve_retry_strategy
from smithy_aws_core.config.sources import EnvironmentSource
from smithy_aws_core.config.validators import (
    ConfigValidationError,
    validate_max_attempts,
    validate_region,
    validate_retry_mode,
)
from smithy_core.config.property import ConfigProperty
from smithy_core.config.resolver import ConfigResolver
from smithy_core.interfaces.config import ConfigSource
from smithy_core.retries import RetryStrategyOptions


class BaseTestConfig:
    """Base config class with common functionality for tests."""

    _resolver: ConfigResolver

    def __init__(self, sources: list[ConfigSource] | None = None) -> None:
        if sources is None:
            sources = [EnvironmentSource()]
        self._resolver = ConfigResolver(sources=sources)

    def get_source(self, key: str) -> str | None:
        cached = self.__dict__.get(f"_cache_{key}")
        return cached[1] if cached else None


def make_config_class(properties: dict[str, ConfigProperty]) -> Any:
    """Factory function to create a config class with specified properties.

    :param properties: Dict mapping property names to ConfigProperty instances

    :returns: A new config class with the specified properties
    """
    class_dict: dict[str, Any] = {
        "__init__": BaseTestConfig.__init__,
        "get_source": BaseTestConfig.get_source,
    }
    class_dict.update(properties)

    return type("TestConfig", (BaseTestConfig,), class_dict)


class TestConfigResolution:
    """Functional tests for complete config resolution flow."""

    def test_environment_var_resolution(self, monkeypatch: MonkeyPatch) -> None:
        TestConfig = make_config_class(
            {"region": ConfigProperty("region", default_value="us-east-1")}
        )
        monkeypatch.setenv("AWS_REGION", "eu-west-1")

        config = TestConfig()

        assert config.region == "eu-west-1"
        assert config.get_source("region") == "environment"

    def test_instance_overrides_environment(self, monkeypatch: MonkeyPatch) -> None:
        TestConfig = make_config_class(
            {"region": ConfigProperty("region", default_value="us-east-1")}
        )

        config = TestConfig()
        config.region = "us-west-2"

        monkeypatch.setenv("AWS_REGION", "eu-west-1")

        assert config.region == "us-west-2"
        assert config.get_source("region") == "instance"

    def test_complex_resolution_with_custom_resolver(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        TestConfig = make_config_class(
            {
                "retry_strategy": ConfigProperty(
                    "retry_strategy",
                    resolver_func=resolve_retry_strategy,
                    default_value=RetryStrategyOptions(retry_mode="standard"),
                )
            }
        )

        monkeypatch.setenv("AWS_RETRY_MODE", "standard")
        monkeypatch.setenv("AWS_MAX_ATTEMPTS", "5")

        config = TestConfig()

        retry_strategy = config.retry_strategy
        assert isinstance(retry_strategy, RetryStrategyOptions)
        assert retry_strategy.retry_mode == "standard"
        assert retry_strategy.max_attempts == 5

        source = config.get_source("retry_strategy")
        assert source == "retry_mode=environment, max_attempts=environment"

    def test_caching_behavior(self, monkeypatch: MonkeyPatch) -> None:
        TestConfig = make_config_class(
            {"region": ConfigProperty("region", default_value="us-east-1")}
        )

        monkeypatch.setenv("AWS_REGION", "ap-south-1")

        config = TestConfig()

        region1 = config.region

        monkeypatch.setenv("AWS_REGION", "eu-central-1")

        region2 = config.region
        # The first value for region which is cached is returned
        assert region1 == region2 == "ap-south-1"

    @pytest.mark.parametrize(
        "property_name,property_config,expected_value",
        [
            (
                "region",
                ConfigProperty("region", default_value="us-east-1"),
                "us-east-1",
            ),
            (
                "retry_mode",
                ConfigProperty(
                    "retry_mode",
                    validator=validate_retry_mode,
                    default_value="standard",
                ),
                "standard",
            ),
        ],
    )
    def test_uses_default_when_no_sources(
        self, property_name: str, property_config: ConfigProperty, expected_value: str
    ) -> None:
        TestConfig = make_config_class({property_name: property_config})
        config = TestConfig(sources=[])

        assert getattr(config, property_name) == expected_value
        assert config.get_source(property_name) == "default"

    def test_default_value_for_complex_resolution(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        TestConfig = make_config_class(
            {
                "retry_strategy": ConfigProperty(
                    "retry_strategy",
                    resolver_func=resolve_retry_strategy,
                    default_value=RetryStrategyOptions(retry_mode="standard"),
                )
            }
        )

        config = TestConfig()

        retry_strategy = config.retry_strategy
        assert isinstance(retry_strategy, RetryStrategyOptions)
        assert retry_strategy.retry_mode == "standard"
        # None for max_attempts means the RetryStrategy will use its
        # own default max_attempts value for the set retry_mode
        assert retry_strategy.max_attempts is None
        source = config.get_source("retry_strategy")
        assert source == "default"

    def test_retry_strategy_combines_multiple_sources(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        TestConfig = make_config_class(
            {
                "retry_strategy": ConfigProperty(
                    "retry_strategy",
                    resolver_func=resolve_retry_strategy,
                    default_value=RetryStrategyOptions(retry_mode="standard"),
                )
            }
        )

        monkeypatch.setenv("AWS_MAX_ATTEMPTS", "10")
        config = TestConfig()

        retry_strategy = config.retry_strategy
        assert retry_strategy.retry_mode == "standard"
        assert retry_strategy.max_attempts == 10
        assert (
            config.get_source("retry_strategy")
            == "retry_mode=default, max_attempts=environment"
        )

    def test_validation_error_when_value_assigned(self) -> None:
        TestConfig = make_config_class(
            {
                "retry_mode": ConfigProperty(
                    "retry_mode",
                    validator=validate_retry_mode,
                    default_value="standard",
                )
            }
        )
        config = TestConfig(sources=[])

        with pytest.raises(ConfigValidationError, match="retry_mode must be one of"):
            config.retry_mode = "invalid_mode"

    def test_validation_error_during_resolution(self, monkeypatch: MonkeyPatch) -> None:
        TestConfig = make_config_class(
            {
                "max_attempts": ConfigProperty(
                    "max_attempts", validator=validate_max_attempts, default_value=3
                )
            }
        )

        monkeypatch.setenv("AWS_MAX_ATTEMPTS", "invalid")

        config = TestConfig()

        with pytest.raises(
            ConfigValidationError, match="max_attempts must be a number"
        ):
            config.max_attempts

    def test_region_validation_fails_when_none(self) -> None:
        TestConfig = make_config_class(
            {"region": ConfigProperty("region", validator=validate_region)}
        )
        config = TestConfig(sources=[])

        with pytest.raises(ConfigValidationError, match="region not found"):
            config.region
