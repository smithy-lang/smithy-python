#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Any
from unittest.mock import Mock

import pytest
from smithy_core import URI
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import Endpoint
from smithy_core.interfaces import URI as URIInterface
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID
from smithy_core.types import TypedProperties
from smithy_http import Fields
from smithy_http.aio import HTTPRequest, HTTPResponse
from smithy_http.aio.interfaces import HTTPRequest as HTTPRequestInterface
from smithy_http.aio.interfaces import HTTPResponse as HTTPResponseInterface
from smithy_http.aio.protocols import HttpBindingClientProtocol, HttpClientProtocol


class MockProtocol(HttpClientProtocol):
    _id = ShapeID("ns.foo#bar")

    @property
    def id(self) -> ShapeID:
        return self._id

    def serialize_request(
        self,
        *,
        operation: APIOperation[Any, Any],
        input: Any,
        endpoint: URIInterface,
        context: TypedProperties,
    ) -> HTTPRequestInterface:
        raise Exception("This is only for tests.")

    def deserialize_response(
        self,
        *,
        operation: APIOperation[Any, Any],
        request: HTTPRequestInterface,
        response: HTTPResponseInterface,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> Any:
        raise Exception("This is only for tests.")


@pytest.mark.parametrize(
    "request_uri,endpoint_uri,expected",
    [
        (
            URI(host="com.example", path="/foo"),
            URI(host="com.example", path="/bar"),
            URI(host="com.example", path="/bar/foo"),
        ),
        (
            URI(host="com.example"),
            URI(host="com.example", path="/bar"),
            URI(host="com.example", path="/bar"),
        ),
        (
            URI(host="com.example", path="/foo"),
            URI(host="com.example"),
            URI(host="com.example", path="/foo"),
        ),
        (
            URI(host="com.example", scheme="http"),
            URI(host="com.example", scheme="https"),
            URI(host="com.example", scheme="https"),
        ),
        (
            URI(host="com.example", username="name", password="password"),
            URI(host="com.example", username="othername", password="otherpassword"),
            URI(host="com.example", username="othername", password="otherpassword"),
        ),
        (
            URI(host="com.example", username="name", password="password"),
            URI(host="com.example"),
            URI(host="com.example", username="name", password="password"),
        ),
        (
            URI(host="com.example", port=8080),
            URI(host="com.example", port=8000),
            URI(host="com.example", port=8000),
        ),
        (
            URI(host="com.example", port=8080),
            URI(host="com.example"),
            URI(host="com.example", port=8080),
        ),
        (
            URI(host="com.example", query="foo=bar"),
            URI(host="com.example"),
            URI(host="com.example", query="foo=bar"),
        ),
        (
            URI(host="com.example"),
            URI(host="com.example", query="spam"),
            URI(host="com.example", query="spam"),
        ),
        (
            URI(host="com.example", query="foo=bar"),
            URI(host="com.example", query="spam"),
            URI(host="com.example", query="spam&foo=bar"),
        ),
        (
            URI(host="com.example", fragment="header"),
            URI(host="com.example", fragment="footer"),
            URI(host="com.example", fragment="footer"),
        ),
        (
            URI(host="com.example"),
            URI(host="com.example", fragment="footer"),
            URI(host="com.example", fragment="footer"),
        ),
        (
            URI(host="com.example", fragment="header"),
            URI(host="com.example"),
            URI(host="com.example", fragment="header"),
        ),
    ],
)
def test_http_protocol_joins_uris(
    request_uri: URI, endpoint_uri: URI, expected: URI
) -> None:
    protocol = MockProtocol()
    request = HTTPRequest(
        destination=request_uri,
        method="GET",
        fields=Fields(),
    )
    endpoint = Endpoint(uri=endpoint_uri)
    updated_request = protocol.set_service_endpoint(request=request, endpoint=endpoint)
    actual = updated_request.destination
    assert actual == expected


@pytest.mark.asyncio
async def test_http_408_creates_timeout_error() -> None:
    """Test that HTTP 408 creates a timeout error with server fault."""
    protocol = Mock(spec=HttpBindingClientProtocol)
    protocol.error_identifier = Mock()
    protocol.error_identifier.identify.return_value = None

    response = HTTPResponse(status=408, fields=Fields())

    error = await HttpBindingClientProtocol._create_error(  # type: ignore[reportPrivateUsage]
        protocol,
        operation=Mock(),
        request=HTTPRequest(
            destination=URI(host="example.com"), method="POST", fields=Fields()
        ),
        response=response,
        response_body=b"",
        error_registry=TypeRegistry({}),
        context=TypedProperties(),
    )

    assert error.is_timeout_error is True
    assert error.fault == "server"
