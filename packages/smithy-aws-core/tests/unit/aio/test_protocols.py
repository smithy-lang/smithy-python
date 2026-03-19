#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import Mock

import pytest
from smithy_aws_core.aio.protocols import (
    AWSErrorIdentifier,
    AWSJSONDocument,
    AwsQueryClientProtocol,
)
from smithy_aws_core.traits import AwsQueryTrait
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, DiscriminatorError, ModeledError
from smithy_core.interfaces import URI
from smithy_core.prelude import STRING
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait
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

    error_identifier = AWSErrorIdentifier()
    actual = error_identifier.identify(
        operation=_mock_operation(_operation_schema("TestOperation")),
        response=http_response,
    )

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


_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.test#TestInput"),
    members={"name": {"target": STRING}},
)
_SERVICE_SCHEMA = Schema.collection(
    id=ShapeID("com.test#QueryService"),
    shape_type=ShapeType.SERVICE,
    traits=[AwsQueryTrait(None)],
)
_INVALID_ACTION_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("com.test#InvalidActionError"),
    traits=[
        Trait.new(id=ShapeID("smithy.api#error"), value="client"),
        Trait.new(
            id=ShapeID("aws.protocols#awsQueryError"),
            value={"code": "InvalidAction"},
        ),
    ],
    members={"message": {"target": STRING}},
)


@dataclass
class _TestInput:
    name: str | None = None

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(_INPUT_SCHEMA, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        if self.name is not None:
            serializer.write_string(_INPUT_SCHEMA.members["name"], self.name)


class _ModeledQueryError(ModeledError):
    message: str

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_ModeledQueryError":
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            if schema.expect_member_name() == "message":
                kwargs["message"] = de.read_string(schema)

        deserializer.read_struct(_INVALID_ACTION_ERROR_SCHEMA, consumer=_consumer)
        return cls(**kwargs)


def _operation_schema(name: str) -> Schema:
    return Schema(
        id=ShapeID(f"com.test#{name}"),
        shape_type=ShapeType.OPERATION,
    )


def _mock_operation(
    schema: Schema,
    *,
    error_schemas: list[Schema] | None = None,
) -> APIOperation[Any, Any]:
    operation = Mock(spec=APIOperation)
    operation.schema = schema
    operation.error_schemas = error_schemas or []
    return cast("APIOperation[Any, Any]", operation)


@pytest.mark.asyncio
async def test_aws_query_serializes_base_request_shape() -> None:
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    request = protocol.serialize_request(
        operation=_mock_operation(_operation_schema("TestOperation")),
        input=_TestInput(name="example"),
        endpoint=cast(URI, Mock()),
        context=TypedProperties(),
    )

    assert request.method == "POST"
    assert request.destination.path == "/"
    assert (
        request.fields["content-type"].as_string()
        == "application/x-www-form-urlencoded"
    )
    body = await request.consume_body_async()
    assert request.fields["content-length"].as_string() == str(len(body))
    assert body == b"Action=TestOperation&Version=2020-01-08&name=example"


def test_aws_query_resolves_modeled_error_from_query_error_trait() -> None:
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    error = getattr(protocol, "_create_error")(
        operation=_mock_operation(
            _operation_schema("FailingOperation"),
            error_schemas=[_INVALID_ACTION_ERROR_SCHEMA],
        ),
        response=HTTPResponse(status=400, fields=tuples_to_fields([])),
        response_body=(
            b"<ErrorResponse><Error><Code>InvalidAction</Code>"
            b"<message>bad request</message></Error></ErrorResponse>"
        ),
        error_registry=TypeRegistry(
            {ShapeID("com.test#InvalidActionError"): _ModeledQueryError}
        ),
    )

    assert isinstance(error, _ModeledQueryError)
    assert error.message == "bad request"


def test_aws_query_resolves_modeled_error_from_default_namespace_fallback() -> None:
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    error = getattr(protocol, "_create_error")(
        operation=_mock_operation(_operation_schema("FailingOperation")),
        response=HTTPResponse(status=503, fields=tuples_to_fields([])),
        response_body=(
            b"<ErrorResponse><Error><Code>ServiceUnavailable</Code>"
            b"<message>try again</message></Error></ErrorResponse>"
        ),
        error_registry=TypeRegistry(
            {ShapeID("com.test#ServiceUnavailable"): _ModeledQueryError}
        ),
    )

    assert isinstance(error, _ModeledQueryError)
    assert error.message == "try again"


def test_aws_query_returns_generic_error_for_unknown_code() -> None:
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    error = getattr(protocol, "_create_error")(
        operation=_mock_operation(_operation_schema("FailingOperation")),
        response=HTTPResponse(status=500, fields=tuples_to_fields([])),
        response_body=(
            b"<ErrorResponse><Error><Code>UnknownThing</Code>"
            b"<message>bad request</message></Error></ErrorResponse>"
        ),
        error_registry=TypeRegistry({}),
    )

    assert isinstance(error, CallError)
    assert not isinstance(error, ModeledError)
    assert error.message == (
        "Unknown error for operation com.test#FailingOperation"
        " - status: 500, code: UnknownThing"
    )
