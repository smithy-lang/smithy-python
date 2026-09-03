#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import Mock

import pytest
from ijson.common import IncompleteJSONError  # type: ignore[reportMissingTypeStubs]
from smithy_aws_core.aio.protocols import (
    AWSErrorIdentifier,
    AwsJson11ClientProtocol,
    AWSJSONDocument,
    AwsQueryClientProtocol,
    RestXmlClientProtocol,
)
from smithy_aws_core.traits import AwsQueryTrait, RestXmlTrait
from smithy_core import URI as _URI
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
from smithy_http.aio import HTTPRequest, HTTPResponse
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


_EMPTY_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.test#EmptyInput"),
)
_EMPTY_OUTPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.test#EmptyOutput"),
)
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
            value={"code": "InvalidAction", "httpResponseCode": 400},
        ),
    ],
    members={"message": {"target": STRING}},
)


@dataclass
class _EmptyInput:
    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(_EMPTY_INPUT_SCHEMA, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        pass


@dataclass
class _EmptyOutput:
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_EmptyOutput":
        deserializer.read_struct(_EMPTY_OUTPUT_SCHEMA, lambda _schema, _de: None)
        return cls()


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


def _aws_json11_protocol() -> AwsJson11ClientProtocol:
    return AwsJson11ClientProtocol(
        Schema(id=ShapeID("com.test#JsonService"), shape_type=ShapeType.SERVICE)
    )


async def test_aws_json11_serializes_base_request_shape() -> None:
    protocol = _aws_json11_protocol()
    request = protocol.serialize_request(
        operation=_mock_operation(_operation_schema("EmptyOperation")),
        input=_EmptyInput(),
        endpoint=_URI(host="example.com"),
        context=TypedProperties(),
    )

    assert request.method == "POST"
    assert request.destination.path == "/"
    assert request.fields["content-type"].as_string() == "application/x-amz-json-1.1"
    assert request.fields["x-amz-target"].as_string() == "JsonService.EmptyOperation"
    assert request.fields["content-length"].as_string() == "2"
    assert await request.consume_body_async() == b"{}"


async def test_aws_json11_resolves_body_error_with_content_type_parameters() -> None:
    protocol = _aws_json11_protocol()
    response = HTTPResponse(
        status=500,
        fields=tuples_to_fields(
            [("content-type", "application/x-amz-json-1.1; charset=utf-8")]
        ),
        body=b'{"__type":"com.test#OtherNsError"}',
    )
    operation = _mock_operation(_operation_schema("FailingOperation"))

    with pytest.raises(_ModeledJSONError):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )


async def test_aws_json11_ignores_body_error_with_unexpected_content_type() -> None:
    protocol = _aws_json11_protocol()
    response = HTTPResponse(
        status=500,
        fields=tuples_to_fields([("content-type", "application/json")]),
        body=b'{"__type":"com.test#OtherNsError"}',
    )
    operation = _mock_operation(_operation_schema("FailingOperation"))

    with pytest.raises(CallError) as exc_info:
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )

    assert not isinstance(exc_info.value, ModeledError)


async def test_aws_json11_deserializes_empty_response_body() -> None:
    protocol = _aws_json11_protocol()
    operation = _mock_operation(_operation_schema("EmptyOperation"))
    cast(Any, operation).output = _EmptyOutput

    output = await protocol.deserialize_response(
        operation=operation,
        request=cast(HTTPRequest, Mock()),
        response=HTTPResponse(status=200, fields=Fields(), body=b""),
        error_registry=TypeRegistry({}),
        context=TypedProperties(),
    )

    assert isinstance(output, _EmptyOutput)


class _ModeledJSONError(ModeledError):
    @classmethod
    def deserialize(cls, deserializer: Any) -> "_ModeledJSONError":
        return cls("modeled JSON error")


async def test_aws_json11_sets_retry_after_on_modeled_error() -> None:
    protocol = _aws_json11_protocol()
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields(
            [
                ("x-amzn-errortype", "com.test#OtherNsError"),
                ("x-amz-retry-after", "1500"),
            ]
        ),
        body=b"",
    )

    with pytest.raises(_ModeledJSONError) as exc_info:
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )

    assert exc_info.value.retry_after == 1.5


async def test_aws_json11_sets_retry_after_on_generic_error() -> None:
    protocol = _aws_json11_protocol()
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=500,
        fields=tuples_to_fields([("x-amz-retry-after", "1500")]),
        body=b"",
    )

    with pytest.raises(CallError) as exc_info:
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry({}),
            context=TypedProperties(),
        )

    assert exc_info.value.retry_after == 1.5


async def test_aws_json11_resolves_modeled_error_from_header_other_namespace() -> None:
    protocol = _aws_json11_protocol()
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

    with pytest.raises(_ModeledJSONError):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.other#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )


async def test_aws_json11_resolves_modeled_error_from_header_only_shapeid() -> None:
    protocol = _aws_json11_protocol()
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields([("x-amzn-errortype", "com.other#OtherNsError")]),
        body=b"",
    )

    with pytest.raises(_ModeledJSONError):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.other#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )


_OTHER_NS_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("com.test#OtherNsError"),
    traits=[Trait.new(id=ShapeID("smithy.api#error"), value="client")],
    members={"message": {"target": STRING}},
)


async def test_aws_json11_resolves_modeled_error_from_header_name_fallback() -> None:
    # The wire error ID carries a different namespace than the modeled error. The
    # awsJson protocols discriminate on shape name only, so it should resolve to the
    # operation's modeled error by matching the shape name.
    protocol = _aws_json11_protocol()
    operation = _mock_operation(
        _operation_schema("FailingOperation"),
        error_schemas=[_OTHER_NS_ERROR_SCHEMA],
    )
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

    with pytest.raises(_ModeledJSONError):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )


async def test_aws_json11_resolves_modeled_error_from_body_name_fallback() -> None:
    # Same as above, but the discriminator comes from the body's __type rather
    # than the x-amzn-errortype header.
    protocol = _aws_json11_protocol()
    operation = _mock_operation(
        _operation_schema("FailingOperation"),
        error_schemas=[_OTHER_NS_ERROR_SCHEMA],
    )
    response = HTTPResponse(
        status=400,
        reason="Bad Request",
        fields=tuples_to_fields([("content-type", "application/x-amz-json-1.1")]),
        body=b'{"__type":"com.wire#OtherNsError"}',
    )

    with pytest.raises(_ModeledJSONError):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#OtherNsError"): _ModeledJSONError}
            ),
            context=TypedProperties(),
        )


async def test_aws_json11_raises_parse_error_for_invalid_error_body() -> None:
    protocol = _aws_json11_protocol()
    operation = _mock_operation(_operation_schema("FailingOperation"))
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields([("content-type", "application/x-amz-json-1.1")]),
        body=b'{"__type":',
    )

    with pytest.raises(IncompleteJSONError, match=r"premature EOF|parse error"):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry({}),
            context=TypedProperties(),
        )


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


async def test_aws_query_resolves_modeled_error_from_query_error_trait() -> None:
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    with pytest.raises(_ModeledQueryError) as exc_info:
        await protocol.deserialize_response(
            operation=_mock_operation(
                _operation_schema("FailingOperation"),
                error_schemas=[_INVALID_ACTION_ERROR_SCHEMA],
            ),
            request=cast(HTTPRequest, Mock()),
            response=HTTPResponse(
                status=400,
                fields=tuples_to_fields([]),
                body=(
                    b"<ErrorResponse><Error><Code>InvalidAction</Code>"
                    b"<message>bad request</message></Error></ErrorResponse>"
                ),
            ),
            error_registry=TypeRegistry(
                {ShapeID("com.test#InvalidActionError"): _ModeledQueryError}
            ),
            context=TypedProperties(),
        )

    assert exc_info.value.message == "bad request"


async def test_aws_query_resolves_modeled_error_from_default_namespace_fallback() -> (
    None
):
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    with pytest.raises(_ModeledQueryError) as exc_info:
        await protocol.deserialize_response(
            operation=_mock_operation(_operation_schema("FailingOperation")),
            request=cast(HTTPRequest, Mock()),
            response=HTTPResponse(
                status=503,
                fields=tuples_to_fields([]),
                body=(
                    b"<ErrorResponse><Error><Code>ServiceUnavailable</Code>"
                    b"<message>try again</message></Error></ErrorResponse>"
                ),
            ),
            error_registry=TypeRegistry(
                {ShapeID("com.test#ServiceUnavailable"): _ModeledQueryError}
            ),
            context=TypedProperties(),
        )

    assert exc_info.value.message == "try again"


async def test_aws_query_returns_generic_error_for_unknown_code() -> None:
    protocol = AwsQueryClientProtocol(_SERVICE_SCHEMA, "2020-01-08")
    with pytest.raises(CallError) as exc_info:
        await protocol.deserialize_response(
            operation=_mock_operation(_operation_schema("FailingOperation")),
            request=cast(HTTPRequest, Mock()),
            response=HTTPResponse(
                status=500,
                fields=tuples_to_fields([]),
                body=(
                    b"<ErrorResponse><Error><Code>UnknownThing</Code>"
                    b"<message>bad request</message></Error></ErrorResponse>"
                ),
            ),
            error_registry=TypeRegistry({}),
            context=TypedProperties(),
        )

    assert not isinstance(exc_info.value, ModeledError)
    assert exc_info.value.message == (
        "Unknown error for operation com.test#FailingOperation"
        " - status: 500, code: UnknownThing"
    )


_REST_XML_SERVICE_SCHEMA = Schema.collection(
    id=ShapeID("com.test#RestXmlService"),
    shape_type=ShapeType.SERVICE,
    traits=[RestXmlTrait(None)],
)
_REST_XML_NAMESPACED_SERVICE_SCHEMA = Schema.collection(
    id=ShapeID("com.test#RestXmlNamespacedService"),
    shape_type=ShapeType.SERVICE,
    traits=[
        RestXmlTrait(None),
        Trait.new(
            id=ShapeID("smithy.api#xmlNamespace"),
            value={"uri": "https://example.com"},
        ),
    ],
)
_REST_XML_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("com.test#InvalidGreeting"),
    traits=[Trait.new(id=ShapeID("smithy.api#error"), value="client")],
    members={
        "Message": {"target": STRING},
        "Header": {
            "target": STRING,
            "traits": [
                Trait.new(id=ShapeID("smithy.api#httpHeader"), value="X-Header")
            ],
        },
    },
)


@dataclass(kw_only=True)
class _ModeledRestXmlError(ModeledError):
    header: str | None = None

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_ModeledRestXmlError":
        kwargs: dict[str, Any] = {"header": None}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_name():
                case "Message":
                    kwargs["message"] = de.read_string(schema)
                case "Header":
                    kwargs["header"] = de.read_string(schema)
                case _:
                    pass

        deserializer.read_struct(_REST_XML_ERROR_SCHEMA, consumer=_consumer)
        return cls(**kwargs)


def _rest_xml_operation_schema(name: str) -> Schema:
    return Schema(
        id=ShapeID(f"com.test#{name}"),
        shape_type=ShapeType.OPERATION,
        traits=[
            Trait.new(
                id=ShapeID("smithy.api#http"),
                value={"method": "PUT", "uri": f"/{name}", "code": 200},
            )
        ],
    )


def _rest_xml_error_registry() -> TypeRegistry:
    return TypeRegistry({ShapeID("com.test#InvalidGreeting"): _ModeledRestXmlError})


async def test_rest_xml_serializes_request_body() -> None:
    protocol = RestXmlClientProtocol(_REST_XML_SERVICE_SCHEMA)
    request = protocol.serialize_request(
        operation=_mock_operation(_rest_xml_operation_schema("TestOperation")),
        input=_TestInput(name="example"),
        endpoint=cast(URI, Mock()),
        context=TypedProperties(),
    )

    assert request.method == "PUT"
    assert request.destination.path == "/TestOperation"
    assert request.fields["content-type"].as_string() == "application/xml"
    body = await request.consume_body_async()
    assert request.fields["content-length"].as_string() == str(len(body))
    assert body == b"<TestInput><name>example</name></TestInput>"


async def test_rest_xml_applies_service_namespace_to_root() -> None:
    protocol = RestXmlClientProtocol(_REST_XML_NAMESPACED_SERVICE_SCHEMA)
    request = protocol.serialize_request(
        operation=_mock_operation(_rest_xml_operation_schema("TestOperation")),
        input=_TestInput(name="example"),
        endpoint=cast(URI, Mock()),
        context=TypedProperties(),
    )

    body = await request.consume_body_async()
    assert body == (
        b'<TestInput xmlns="https://example.com"><name>example</name></TestInput>'
    )


async def test_rest_xml_omits_body_for_empty_input() -> None:
    protocol = RestXmlClientProtocol(_REST_XML_SERVICE_SCHEMA)
    request = protocol.serialize_request(
        operation=_mock_operation(_rest_xml_operation_schema("TestOperation")),
        input=_EmptyInput(),
        endpoint=cast(URI, Mock()),
        context=TypedProperties(),
    )

    assert "content-type" not in request.fields
    assert await request.consume_body_async() == b""


async def _raise_rest_xml_error(
    body: bytes,
    *,
    status: int = 400,
    headers: list[tuple[str, str]] | None = None,
    error_schemas: list[Schema] | None = None,
    error_registry: TypeRegistry | None = None,
) -> None:
    protocol = RestXmlClientProtocol(_REST_XML_SERVICE_SCHEMA)
    await protocol.deserialize_response(
        operation=_mock_operation(
            _rest_xml_operation_schema("FailingOperation"),
            error_schemas=error_schemas,
        ),
        request=cast(HTTPRequest, Mock()),
        response=HTTPResponse(
            status=status,
            fields=tuples_to_fields(headers or []),
            body=body,
        ),
        error_registry=error_registry
        if error_registry is not None
        else _rest_xml_error_registry(),
        context=TypedProperties(),
    )


async def test_rest_xml_resolves_wrapped_error_with_http_bindings() -> None:
    with pytest.raises(_ModeledRestXmlError) as exc_info:
        await _raise_rest_xml_error(
            b"<ErrorResponse><Error><Type>Sender</Type><Code>InvalidGreeting</Code>"
            b"<Message>Hi</Message></Error><RequestId>foo-id</RequestId>"
            b"</ErrorResponse>",
            headers=[("Content-Type", "application/xml"), ("X-Header", "hdr")],
        )

    assert exc_info.value.message == "Hi"
    assert exc_info.value.header == "hdr"


async def test_rest_xml_resolves_unwrapped_error() -> None:
    with pytest.raises(_ModeledRestXmlError) as exc_info:
        await _raise_rest_xml_error(
            b"<Error><Code>InvalidGreeting</Code><Message>Hi</Message></Error>",
        )

    assert exc_info.value.message == "Hi"


async def test_rest_xml_resolves_error_from_operation_errors_other_namespace() -> None:
    error_schema = Schema.collection(
        id=ShapeID("com.other#InvalidGreeting"),
        members={"Message": {"target": STRING}},
    )
    with pytest.raises(_ModeledRestXmlError) as exc_info:
        await _raise_rest_xml_error(
            b"<Error><Code>InvalidGreeting</Code><Message>Hi</Message></Error>",
            error_schemas=[error_schema],
            error_registry=TypeRegistry({error_schema.id: _ModeledRestXmlError}),
        )

    assert exc_info.value.message == "Hi"


async def test_rest_xml_resolves_error_from_header() -> None:
    with pytest.raises(_ModeledRestXmlError) as exc_info:
        await _raise_rest_xml_error(
            b"<ErrorResponse><Error><Message>Hi</Message></Error></ErrorResponse>",
            headers=[("x-amzn-errortype", "InvalidGreeting")],
        )

    assert exc_info.value.message == "Hi"


async def test_rest_xml_sets_retry_after_on_modeled_error() -> None:
    with pytest.raises(_ModeledRestXmlError) as exc_info:
        await _raise_rest_xml_error(
            b"<Error><Code>InvalidGreeting</Code><Message>Hi</Message></Error>",
            status=429,
            headers=[("x-amz-retry-after", "3000")],
        )

    assert exc_info.value.retry_after == 3


async def test_rest_xml_returns_generic_error_for_unknown_code() -> None:
    with pytest.raises(CallError) as exc_info:
        await _raise_rest_xml_error(
            b"<ErrorResponse><Error><Code>UnknownThing</Code></Error></ErrorResponse>",
            status=500,
        )

    assert not isinstance(exc_info.value, ModeledError)
    assert exc_info.value.fault == "server"
    assert exc_info.value.message == (
        "Unknown error for operation com.test#FailingOperation"
        " - status: 500 - code: UnknownThing"
    )


async def test_rest_xml_returns_generic_error_for_non_xml_body() -> None:
    with pytest.raises(CallError) as exc_info:
        await _raise_rest_xml_error(b"<html>nope</html>", status=503)

    assert not isinstance(exc_info.value, ModeledError)
    assert exc_info.value.message == (
        "Unknown error for operation com.test#FailingOperation - status: 503"
    )
