#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from smithy_aws_core.interceptors.api_gateway import ApiGatewayAcceptHeaderInterceptor
from smithy_core import URI
from smithy_core.interceptors import RequestContext
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest


def _request(fields: Fields) -> HTTPRequest:
    destination = URI(host="apigateway.us-east-1.amazonaws.com", path="/restapis")
    return HTTPRequest(destination=destination, method="GET", fields=fields)


def test_sets_accept_header() -> None:
    interceptor = ApiGatewayAcceptHeaderInterceptor()
    request = _request(Fields())
    context = RequestContext(
        request=Mock(), properties=TypedProperties(), transport_request=request
    )

    result = interceptor.modify_before_signing(context)

    assert result.fields["Accept"].values == ["application/json"]


def test_overwrites_existing_accept_header() -> None:
    interceptor = ApiGatewayAcceptHeaderInterceptor()
    fields = Fields([Field(name="Accept", values=["application/hal+json"])])
    request = _request(fields)
    context = RequestContext(
        request=Mock(), properties=TypedProperties(), transport_request=request
    )

    result = interceptor.modify_before_signing(context)

    assert result.fields["Accept"].values == ["application/json"]
