# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_aws_core.config.resolver import ConfigResolver
from smithy_aws_core.config.source_info import SimpleSource


class StubSource:
    """A simple ConfigSource implementation for testing.

    Returns values from a provided dictionary, or None if the key
    is not present.
    """

    def __init__(self, source_name: str, data: dict[str, Any] | None = None):
        self._name = source_name
        self._data = data or {}

    @property
    def name(self) -> str:
        return self._name

    def get(self, key: str) -> Any | None:
        return self._data.get(key)


class TestConfigResolver:
    def test_returns_value_from_single_source(self):
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])

        result = resolver.get("region")

        assert result == ("us-west-2", SimpleSource("environment"))

    def test_returns_None_when_source_has_no_value(self):
        source = StubSource("environment", {})
        resolver = ConfigResolver(sources=[source])

        result = resolver.get("region")

        assert result == (None, None)

    def test_returns_None_with_empty_source_list(self):
        resolver = ConfigResolver(sources=[])

        result = resolver.get("region")

        assert result == (None, None)

    def test_first_source_takes_precedence(self):
        first_priority_source = StubSource("source_one", {"region": "us-east-1"})
        second_priority_source = StubSource("source_two", {"region": "eu-west-1"})
        resolver = ConfigResolver(
            sources=[first_priority_source, second_priority_source]
        )

        result = resolver.get("region")

        assert result == ("us-east-1", SimpleSource("source_one"))

    def test_skips_source_returning_none_and_uses_next(self):
        empty_source = StubSource("source_one", {})
        fallback_source = StubSource("source_two", {"region": "ap-south-1"})
        resolver = ConfigResolver(sources=[empty_source, fallback_source])

        result = resolver.get("region")

        assert result == ("ap-south-1", SimpleSource("source_two"))

    def test_resolves_different_keys_from_different_sources(self):
        instance = StubSource("source_one", {"region": "us-west-2"})
        environment = StubSource("source_two", {"retry_mode": "adaptive"})
        resolver = ConfigResolver(sources=[instance, environment])

        region = resolver.get("region")
        retry_mode = resolver.get("retry_mode")

        assert region == ("us-west-2", SimpleSource("source_one"))
        assert retry_mode == ("adaptive", SimpleSource("source_two"))

    def test_returns_non_string_values(self):
        source = StubSource(
            "default",
            {
                "max_retries": 3,
                "use_ssl": True,
            },
        )
        resolver = ConfigResolver(sources=[source])

        assert resolver.get("max_retries") == (3, SimpleSource("default"))
        assert resolver.get("use_ssl") == (True, SimpleSource("default"))

    def test_get_is_idempotent(self):
        source = StubSource("environment", {"region": "us-west-2"})
        resolver = ConfigResolver(sources=[source])

        result1 = resolver.get("region")
        result2 = resolver.get("region")
        result3 = resolver.get("region")

        assert (
            result1 == result2 == result3 == ("us-west-2", SimpleSource("environment"))
        )

    def test_treats_empty_string_as_valid_value(self):
        source = StubSource("test", {"region": ""})
        resolver = ConfigResolver(sources=[source])

        value, source_name = resolver.get("region")

        assert value == ""
        assert source_name == SimpleSource("test")
