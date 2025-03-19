#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from unittest.mock import Mock

import pytest

from smithy_core import URI
from smithy_core.endpoints import STATIC_URI, EndpointResolverParams
from smithy_core.types import TypedProperties
from smithy_core.exceptions import EndpointResolutionError

from smithy_aws_core import REGION
from smithy_aws_core.endpoints.standard_regional import (
    StandardRegionalEndpointsResolver,
)


async def test_resolve_endpoint_with_valid_sdk_endpoint_string():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties(
        {STATIC_URI.key: "https://example.com/path?query=123"}
    )

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri.host == "example.com"
    assert endpoint.uri.path == "/path"
    assert endpoint.uri.scheme == "https"
    assert endpoint.uri.query == "query=123"


async def test_resolve_endpoint_with_sdk_endpoint_uri():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    parsed_uri = URI(
        host="example.com", path="/path", scheme="https", query="query=123", port=443
    )
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties({STATIC_URI.key: parsed_uri})

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri == parsed_uri


async def test_resolve_endpoint_with_invalid_sdk_endpoint():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties({STATIC_URI.key: "invalid_uri"})

    with pytest.raises(EndpointResolutionError):
        await resolver.resolve_endpoint(params)


async def test_resolve_endpoint_with_region():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties({REGION.key: "us-west-2"})

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri.host == "service.us-west-2.amazonaws.com"


async def test_resolve_endpoint_with_no_sdk_endpoint_or_region():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties()

    with pytest.raises(EndpointResolutionError):
        await resolver.resolve_endpoint(params)


async def test_resolve_endpoint_with_sdk_endpoint_and_region():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = Mock(spec=EndpointResolverParams)
    params.context = TypedProperties(
        {STATIC_URI.key: "https://example.com", REGION.key: "us-west-2"}
    )

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri.host == "example.com"
