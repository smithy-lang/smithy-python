# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

from smithy_core import URI
from smithy_core.aio.endpoints import StaticEndpointResolver
from smithy_core.endpoints import STATIC_ENDPOINT_CONFIG, EndpointResolverParams
from smithy_core.types import TypedProperties


@dataclass
class EndpointConfig:
    endpoint_uri: str | URI | None = None

    @classmethod
    def params(
        cls, endpoint_uri: str | URI | None = None
    ) -> EndpointResolverParams[Any]:
        params = Mock(spec=EndpointResolverParams)
        params.context = TypedProperties(
            {STATIC_ENDPOINT_CONFIG.key: cls(endpoint_uri)}
        )
        return params


async def test_endpoint_provider_with_uri_string() -> None:
    params = EndpointConfig.params("https://foo.example.com:8080/spam?foo=bar&foo=baz")
    expected = URI(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query="foo=bar&foo=baz",
        port=8080,
    )
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.uri == expected


async def test_endpoint_provider_with_uri_object() -> None:
    expected = URI(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query="foo=bar&foo=baz",
        port=8080,
    )
    params = EndpointConfig.params(expected)
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.uri == expected
