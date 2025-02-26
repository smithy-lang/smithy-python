#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core import URI
from smithy_http import Fields
from smithy_http.aio.endpoints import StaticEndpointResolver
from smithy_http.endpoints import StaticEndpointParams


async def test_endpoint_provider_with_uri_string() -> None:
    params = StaticEndpointParams(
        uri="https://foo.example.com:8080/spam?foo=bar&foo=baz"
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
    assert result.headers == Fields([])


async def test_endpoint_provider_with_uri_object() -> None:
    expected = URI(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query="foo=bar&foo=baz",
        port=8080,
    )
    params = StaticEndpointParams(uri=expected)
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.uri == expected
    assert result.headers == Fields([])
