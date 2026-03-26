#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import Mock

import pytest
from smithy_aws_core.aio.protocols import (
    AWSErrorIdentifier,
    AwsJson11ClientProtocol,
    AWSJSONDocument,
    RestJsonClientProtocol,
)
from smithy_core import URI
from smithy_core.aio.interfaces import AsyncWriter
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import DiscriminatorError, ModeledError
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    HTTPTrait,
    StreamingTrait,
)
from smithy_core.types import TypedProperties
from smithy_http import Fields, tuples_to_fields
from smithy_http.aio import HTTPResponse
from smithy_json import JSONSettings


@pytest.mark.parametrize(
    "header, expected",
    [
        ("FooError", "com.test#FooError"),
        (
            "FooError:http://internal.amazon.com/coral/com.amazon.coral.validate/",
            "com.test#FooError",
        ),
        (
            "com.test#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate",
            "com.test#FooError",
        ),
        ("com.other#FooError", "com.other#FooError"),
        ("", None),
        (":", None),
        (None, None),
    ],
)
def test_aws_error_identifier(header: str | None, expected: ShapeID | None) -> None:
    fields = Fields()
    if header is not None:
        fields = tuples_to_fields([("x-amzn-errortype", header)])
    http_response = HTTPResponse(status=500, fields=fields)

    operation = Mock(spec=APIOperation)
    operation.schema = Schema(
        id=ShapeID("com.test#TestOperation"), shape_type=ShapeType.OPERATION
    )

    error_identifier = AWSErrorIdentifier()
    actual = error_identifier.identify(operation=operation, response=http_response)

    assert actual == expected


@pytest.mark.parametrize(
    "document, expected",
    [
        ({"__type": "FooError"}, "com.test#FooError"),
        ({"__type": "com.test#FooError"}, "com.test#FooError"),
        (
            {
                "__type": "FooError:http://internal.amazon.com/coral/com.amazon.coral.validate/"
            },
            "com.test#FooError",
        ),
        (
            {
                "__type": "com.test#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate"
            },
            "com.test#FooError",
        ),
        ({"code": "FooError"}, "com.test#FooError"),
        ({"code": "com.test#FooError"}, "com.test#FooError"),
        (
            {
                "code": "FooError:http://internal.amazon.com/coral/com.amazon.coral.validate/"
            },
            "com.test#FooError",
        ),
        (
            {
                "code": "com.test#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate"
            },
            "com.test#FooError",
        ),
        ({"__type": "FooError", "code": "BarError"}, "com.test#FooError"),
        ("FooError", None),
        ({"__type": None}, None),
        ({"__type": ""}, None),
        ({"__type": ":"}, None),
    ],
)
def test_aws_json_document_discriminator(
    document: dict[str, str], expected: ShapeID | None
) -> None:
    settings = JSONSettings(
        document_class=AWSJSONDocument, default_namespace="com.test"
    )
    if expected is None:
        with pytest.raises(DiscriminatorError):
            AWSJSONDocument(document, settings=settings).discriminator
    else:
        discriminator = AWSJSONDocument(document, settings=settings).discriminator
        assert discriminator == expected


_EMPTY_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.test#EmptyInput"),
)
_EVENT_STREAM_MEMBER_SCHEMA = Schema(
    id=ShapeID("com.test#InputEvents"),
    shape_type=ShapeType.UNION,
    traits=[StreamingTrait()],
)


@dataclass
class _EmptyInput:
    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(_EMPTY_INPUT_SCHEMA, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        pass


def _operation_schema(name: str) -> Schema:
    return Schema(
        id=ShapeID(f"com.test#{name}"),
        shape_type=ShapeType.OPERATION,
    )


def _http_operation_schema(name: str) -> Schema:
    return Schema(
        id=ShapeID(f"com.test#{name}"),
        shape_type=ShapeType.OPERATION,
        traits=[HTTPTrait({"method": "POST", "uri": "/"})],
    )


def _mock_operation(schema: Schema) -> APIOperation[Any, Any]:
    operation = Mock(spec=APIOperation)
    operation.schema = schema
    return cast("APIOperation[Any, Any]", operation)


@pytest.mark.asyncio
async def test_aws_json11_serializes_base_request_shape() -> None:
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    request = protocol.serialize_request(
        operation=_mock_operation(_operation_schema("EmptyOperation")),
        input=_EmptyInput(),
        endpoint=URI(host="example.com"),
        context=TypedProperties(),
    )

    assert request.method == "POST"
    assert request.destination.path == "/"
    assert request.fields["content-type"].as_string() == "application/x-amz-json-1.1"
    assert request.fields["x-amz-target"].as_string() == "JsonService.EmptyOperation"
    assert request.fields["content-length"].as_string() == "2"
    assert await request.consume_body_async() == b"{}"


@pytest.mark.asyncio
async def test_aws_json11_serializes_input_event_stream_request_with_writable_body() -> (
    None
):
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_operation_schema("StreamingOperation"))
    cast(Any, operation).input_stream_member = _EVENT_STREAM_MEMBER_SCHEMA

    request = protocol.serialize_request(
        operation=operation,
        input=_EmptyInput(),
        endpoint=URI(host="example.com"),
        context=TypedProperties(),
    )

    assert (
        request.fields["content-type"].as_string()
        == "application/vnd.amazon.eventstream"
    )
    assert "content-length" not in request.fields
    assert isinstance(request.body, AsyncWriter)


def test_aws_json_matches_content_type_with_parameters() -> None:
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    response = HTTPResponse(
        status=500,
        fields=tuples_to_fields(
            [("content-type", "application/x-amz-json-1.1; charset=utf-8")]
        ),
    )
    assert getattr(protocol, "_matches_content_type")(response)


class _OtherNamespaceModeledError(ModeledError):
    @classmethod
    def deserialize(cls, deserializer: Any) -> "_OtherNamespaceModeledError":
        return cls("other namespace")


@pytest.mark.asyncio
async def test_aws_json11_resolves_modeled_error_from_header_other_namespace() -> None:
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields(
            [
                ("x-amzn-errortype", "com.other#OtherNsError"),
                ("content-type", "application/x-amz-json-1.1"),
            ]
        ),
        body=b'{"__type":"com.other#OtherNsError"}',
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.other#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)


@pytest.mark.asyncio
async def test_aws_json11_resolves_modeled_error_from_header_only_shapeid() -> None:
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields([("x-amzn-errortype", "com.other#OtherNsError")]),
        body=b"",
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.other#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)


@pytest.mark.asyncio
async def test_aws_json11_resolves_modeled_error_from_header_default_namespace_fallback() -> (
    None
):
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields(
            [
                ("x-amzn-errortype", "com.wire#OtherNsError"),
                ("content-type", "application/x-amz-json-1.1"),
            ]
        ),
        body=b'{"__type":"com.wire#OtherNsError"}',
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.test#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)


@pytest.mark.asyncio
async def test_aws_json11_resolves_modeled_error_from_body_default_namespace_fallback() -> (
    None
):
    protocol = AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields([("content-type", "application/x-amz-json-1.1")]),
        body=b'{"__type":"com.wire#OtherNsError"}',
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.test#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)


@pytest.mark.asyncio
async def test_rest_json_resolves_modeled_error_from_header_only_shapeid() -> None:
    protocol = RestJsonClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_http_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields([("x-amzn-errortype", "com.other#OtherNsError")]),
        body=b"",
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.other#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)


@pytest.mark.asyncio
async def test_rest_json_resolves_modeled_error_from_header_default_namespace_fallback() -> (
    None
):
    protocol = RestJsonClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_http_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields(
            [
                ("x-amzn-errortype", "com.wire#OtherNsError"),
                ("content-type", "application/json"),
            ]
        ),
        body=b'{"__type":"com.wire#OtherNsError"}',
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.test#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)


@pytest.mark.asyncio
async def test_rest_json_resolves_modeled_error_from_body_default_namespace_fallback() -> (
    None
):
    protocol = RestJsonClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )
    operation = _mock_operation(_http_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields([("content-type", "application/json")]),
        body=b'{"__type":"com.wire#OtherNsError"}',
    )

    error = await getattr(protocol, "_create_error")(
        operation=operation,
        request=Mock(),
        response=response,
        response_body=response.body,
        error_registry=TypeRegistry(
            {ShapeID("com.test#OtherNsError"): _OtherNamespaceModeledError}
        ),
        context=TypedProperties(),
    )

    assert isinstance(error, _OtherNamespaceModeledError)
