# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any, NoReturn

import pytest
from smithy_core.config.property import ConfigProperty
from smithy_core.config.resolver import ConfigResolver


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


class StubConfig:
    """A minimal Config class for testing ConfigProperty descriptor."""

    region = ConfigProperty("region")
    retry_mode = ConfigProperty("retry_mode")

    def __init__(self, resolver: ConfigResolver) -> None:
        self._resolver = resolver


class TestConfigPropertyDescriptor:
    def test_resolves_value_from_resolver_on_first_access(self) -> None:
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        result = config.region

        assert result == "us-west-2"

    def test_caches_resolved_value(self) -> None:
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        # First access
        result1 = config.region
        # Second access
        result2 = config.region

        assert result1 == result2 == "us-west-2"
        # Verify it's cached in __dict__ of config object
        assert "_cache_region" in config.__dict__

    def test_returns_none_when_value_unresolved(self) -> None:
        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        result = config.region

        assert result is None

    def test_caches_none_for_unresolved_values(self) -> None:
        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        # First access
        result1 = config.region
        # Second access
        result2 = config.region

        assert result1 is None
        assert result2 is None
        # Verify it's cached
        assert "_cache_region" in config.__dict__
        assert config.__dict__["_cache_region"] == (None, None)

    def test_different_properties_resolve_independently(self) -> None:
        source = StubSource(
            "environment", {"region": "us-west-2", "retry_mode": "adaptive"}
        )
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        region = config.region
        retry_mode = config.retry_mode

        assert region == "us-west-2"
        assert retry_mode == "adaptive"


class TestConfigPropertyValidation:
    """Test suite for ConfigProperty validation behavior."""

    def _create_config_with_validator(
        self, validator: Callable[[Any, str | None], Any]
    ) -> type[Any]:
        """Helper to create a config class with a specific validator."""

        class ConfigWithValidator:
            region = ConfigProperty("region", validator=validator)

            def __init__(self, resolver: ConfigResolver) -> None:
                self._resolver = resolver

        return ConfigWithValidator

    def test_calls_validator_on_resolution(self) -> None:
        call_log: list[tuple[Any, str | None]] = []

        def mock_validator(value: Any, source: str | None) -> Any:
            call_log.append((value, source))
            return value

        ConfigWithValidator = self._create_config_with_validator(mock_validator)
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = ConfigWithValidator(resolver)

        result = config.region

        assert result == "us-west-2"
        assert len(call_log) == 1
        assert call_log[0] == ("us-west-2", "environment")

    def test_validator_exception_propagates(self) -> None:
        def failing_validator(value: Any, source: str | None) -> NoReturn:
            raise ValueError("Invalid value")

        ConfigWithValidator = self._create_config_with_validator(failing_validator)
        source = StubSource("environment", {"region": "invalid-region-123"})
        resolver = ConfigResolver(sources=[source])
        config = ConfigWithValidator(resolver)

        with pytest.raises(ValueError, match="Invalid value"):
            _ = config.region

    def test_validator_not_called_on_cached_access(self) -> None:
        call_count = 0

        def counting_validator(value: Any, source: str | None) -> Any:
            nonlocal call_count
            call_count += 1
            return value

        ConfigWithValidator = self._create_config_with_validator(counting_validator)
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = ConfigWithValidator(resolver)

        # Multiple accesses
        _ = config.region
        _ = config.region
        _ = config.region

        # Only the first call accessed the validator
        assert call_count == 1  # Validator called only once


class TestConfigPropertySetter:
    """Test suite for ConfigProperty setter behavior."""

    def test_set_value_marks_source_as_instance(self) -> None:
        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        config.region = "eu-west-1"

        # Check the cached tuple
        assert config.__dict__["_cache_region"] == ("eu-west-1", "instance")

    def test_value_set_after_resolution_marks_source_as_plugin(self) -> None:
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        # First access triggers resolution from environment source
        _ = config.region

        # Modify after resolution
        config.region = "eu-west-1"

        # Verify the new value is returned
        assert config.region == "eu-west-1"
        # Verify source is marked as 'plugin'
        # Any config value modified after initialization will have 'plugin' for source
        assert config.__dict__["_cache_region"] == ("eu-west-1", "plugin")

    def test_validator_is_called_when_setting_values(self) -> None:
        call_log: list[tuple[Any, str | None]] = []

        def mock_validator(value: Any, source: str | None) -> Any:
            call_log.append((value, source))
            return value

        class ConfigWithValidator:
            region = ConfigProperty("region", validator=mock_validator)

            def __init__(self, resolver: ConfigResolver) -> None:
                self._resolver = resolver

        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])
        config = ConfigWithValidator(resolver)

        config.region = "us-west-2"

        assert config.region == "us-west-2"
        assert len(call_log) == 1
        assert call_log[0] == ("us-west-2", "instance")

    def test_validator_throws_exception_when_setting_invalid_value(self) -> None:
        def mock_failing_validation(value: Any, source: str | None) -> NoReturn:
            raise ValueError("Invalid value")

        class ConfigWithValidator:
            region = ConfigProperty("region", validator=mock_failing_validation)

            def __init__(self, resolver: ConfigResolver) -> None:
                self._resolver = resolver

        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])
        config = ConfigWithValidator(resolver)

        with pytest.raises(ValueError, match="Invalid value"):
            config.region = "some-invalid-2"

    def test_set_overrides_resolved_value(self) -> None:
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        # First access resolves from environment
        assert config.region == "us-west-2"

        # Setting overrides
        config.region = "eu-west-1"

        assert config.region == "eu-west-1"


class TestConfigPropertyCaching:
    """Test suite for ConfigProperty caching implementation details."""

    def test_cache_stores_value_and_source_as_tuple(self) -> None:
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        _ = config.region

        cached: Any = config.__dict__["_cache_region"]
        assert cached == ("us-west-2", "environment")

    def test_cache_key_is_unique_per_property(self) -> None:
        source = StubSource(
            "environment", {"region": "us-west-2", "retry_mode": "adaptive"}
        )
        resolver = ConfigResolver(sources=[source])
        config = StubConfig(resolver)

        _ = config.region
        _ = config.retry_mode

        assert "_cache_region" in config.__dict__
        assert "_cache_retry_mode" in config.__dict__
        assert config.__dict__["_cache_region"] != config.__dict__["_cache_retry_mode"]
