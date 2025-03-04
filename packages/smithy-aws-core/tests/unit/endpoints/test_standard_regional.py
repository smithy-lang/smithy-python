#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_aws_core.endpoints.standard_regional import (
    StandardRegionalEndpointsResolver,
    RegionalEndpointParameters,
)

from smithy_core import URI
from smithy_http.endpoints import EndpointResolutionError

import pytest


async def test_resolve_endpoint_with_valid_sdk_endpoint_string():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = RegionalEndpointParameters(
        sdk_endpoint="https://example.com/path?query=123", region=None
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
    params = RegionalEndpointParameters(sdk_endpoint=parsed_uri, region=None)

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri == parsed_uri


async def test_resolve_endpoint_with_invalid_sdk_endpoint():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = RegionalEndpointParameters(sdk_endpoint="invalid-uri", region=None)

    with pytest.raises(EndpointResolutionError):
        await resolver.resolve_endpoint(params)


async def test_resolve_endpoint_with_region():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = RegionalEndpointParameters(sdk_endpoint=None, region="us-west-2")

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri.host == "service.us-west-2.amazonaws.com"


async def test_resolve_endpoint_with_no_sdk_endpoint_or_region():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = RegionalEndpointParameters(sdk_endpoint=None, region=None)

    with pytest.raises(EndpointResolutionError):
        await resolver.resolve_endpoint(params)


async def test_resolve_endpoint_with_sdk_endpoint_and_region():
    resolver = StandardRegionalEndpointsResolver(endpoint_prefix="service")
    params = RegionalEndpointParameters(
        sdk_endpoint="https://example.com", region="us-west-2"
    )

    endpoint = await resolver.resolve_endpoint(params)

    assert endpoint.uri.host == "example.com"
