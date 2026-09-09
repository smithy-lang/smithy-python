#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Self

import pytest
from smithy_core import URI
from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import Endpoint
from smithy_core.interfaces import TypedProperties as TypedPropertiesInterface
from smithy_core.interfaces import URI as URIInterface
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import HTTPTrait
from smithy_core.types import TypedProperties
from smithy_http import Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.interfaces import (
    HTTPErrorIdentifier,
)
from smithy_http.aio.interfaces import (
    HTTPRequest as HTTPRequestInterface,
)
from smithy_http.aio.interfaces import (
    HTTPResponse as HTTPResponseInterface,
)
from smithy_http.aio.protocols import HttpBindingClientProtocol, HttpClientProtocol
from smithy_json import JSONCodec


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
        context: TypedPropertiesInterface,
    ) -> HTTPRequestInterface:
        raise Exception("This is only for tests.")

    def deserialize_response(
        self,
        *,
        operation: APIOperation[Any, Any],
        request: HTTPRequestInterface,
        response: HTTPResponseInterface,
        error_registry: TypeRegistry,
        context: TypedPropertiesInterface,
    ) -> Any:
        raise Exception("This is only for tests.")


class MockBindingProtocol(HttpBindingClientProtocol):
    _id = ShapeID("ns.foo#binding")
    _codec = JSONCodec()
    _error_identifier = HTTPErrorIdentifier()

    @property
    def id(self) -> ShapeID:
        return self._id

    @property
    def payload_codec(self) -> Codec:
        return self._codec

    @property
    def content_type(self) -> str:
        return "application/json"

    @property
    def error_identifier(self) -> HTTPErrorIdentifier:
        return self._error_identifier


class LegacyInput:
    SCHEMA = Schema.collection(id=ShapeID("ns.foo#LegacyInput"))

    def __init__(self) -> None:
        self.serialize_called = False

    def serialize(self, serializer: ShapeSerializer) -> None:
        self.serialize_called = True
        with serializer.begin_struct(self.SCHEMA):
            pass


class StructInput:
    SCHEMA = Schema.collection(id=ShapeID("ns.foo#StructInput"))

    def __init__(self) -> None:
        self.serialize_members_called = False

    def serialize(self, serializer: ShapeSerializer) -> None:
        raise AssertionError("The structure fast path must not call serialize().")

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        self.serialize_members_called = True


class MockOutput:
    SCHEMA = Schema.collection(id=ShapeID("ns.foo#MockOutput"))

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls()


def test_http_binding_protocol_falls_back_to_legacy_serialize() -> None:
    operation = APIOperation(
        input=LegacyInput,
        output=MockOutput,
        schema=Schema(
            id=ShapeID("ns.foo#LegacyOperation"),
            shape_type=ShapeType.OPERATION,
            traits=[HTTPTrait({"method": "POST", "code": 200, "uri": "/legacy"})],
        ),
        input_schema=LegacyInput.SCHEMA,
        output_schema=MockOutput.SCHEMA,
        error_registry=TypeRegistry({}),
        effective_auth_schemes=[],
        error_schemas=[],
    )
    input = LegacyInput()

    request = MockBindingProtocol().serialize_request(
        operation=operation,
        input=input,
        endpoint=URI(host="example.com"),
        context=TypedProperties(),
    )

    assert input.serialize_called
    assert request.method == "POST"
    assert request.destination.path == "/legacy"


def test_http_binding_protocol_uses_structure_fast_path() -> None:
    operation = APIOperation(
        input=StructInput,
        output=MockOutput,
        schema=Schema(
            id=ShapeID("ns.foo#StructOperation"),
            shape_type=ShapeType.OPERATION,
            traits=[HTTPTrait({"method": "POST", "code": 200, "uri": "/structure"})],
        ),
        input_schema=StructInput.SCHEMA,
        output_schema=MockOutput.SCHEMA,
        error_registry=TypeRegistry({}),
        effective_auth_schemes=[],
        error_schemas=[],
    )
    input = StructInput()

    request = MockBindingProtocol().serialize_request(
        operation=operation,
        input=input,
        endpoint=URI(host="example.com"),
        context=TypedProperties(),
    )

    assert input.serialize_members_called
    assert request.method == "POST"
    assert request.destination.path == "/structure"


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
        (
            URI(host="foo."),
            URI(host="com.example"),
            URI(host="com.example"),
        ),
        (
            URI(host="."),
            URI(host="com.example"),
            URI(host="com.example"),
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
