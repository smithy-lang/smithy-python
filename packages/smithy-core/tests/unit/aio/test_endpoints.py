# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import Mock
from smithy_core.types import TypedProperties
from smithy_core.endpoints import EndpointResolverParams, STATIC_URI
from smithy_core.aio.endpoints import StaticEndpointResolver
from smithy_core import URI


async def test_endpoint_provider_with_uri_string() -> None:
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties(
        {STATIC_URI.key: "https://foo.example.com:8080/spam?foo=bar&foo=baz"}
    )
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
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties({STATIC_URI.key: expected})
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.uri == expected
