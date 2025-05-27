#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Any

import pytest
from smithy_core import URI
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import Endpoint
from smithy_core.interfaces import TypedProperties
from smithy_core.interfaces import URI as URIInterface
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID
from smithy_http import Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.interfaces import HTTPRequest as HTTPRequestInterface
from smithy_http.aio.interfaces import HTTPResponse as HTTPResponseInterface
from smithy_http.aio.protocols import HttpClientProtocol


class TestProtocol(HttpClientProtocol):
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
    protocol = TestProtocol()
    request = HTTPRequest(
        destination=request_uri,
        method="GET",
        fields=Fields(),
    )
    endpoint = Endpoint(uri=endpoint_uri)
    updated_request = protocol.set_service_endpoint(request=request, endpoint=endpoint)
    actual = updated_request.destination
    assert actual == expected
