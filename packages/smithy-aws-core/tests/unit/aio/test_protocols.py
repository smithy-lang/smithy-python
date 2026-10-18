#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import gzip
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch
from xml.etree import ElementTree

import pytest
from aws_sdk_signers import AsyncSigV4Signer, AWSRequest, SigV4SigningProperties
from ijson.common import IncompleteJSONError  # type: ignore[reportMissingTypeStubs]
from smithy_aws_core.aio.protocols import (
    AWSErrorIdentifier,
    AwsJson11ClientProtocol,
    AWSJSONDocument,
    AwsQueryClientProtocol,
    RestXmlClientProtocol,
)
from smithy_aws_core.auth import SigV4AuthScheme
from smithy_aws_core.auth.sigv4 import SigV4Signer
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_aws_core.identity.static import StaticCredentialsResolver
from smithy_aws_event_stream.events import EventMessage
from smithy_core import URI as _URI
from smithy_core.aio.client import ClientCall, RequestPipeline
from smithy_core.aio.interfaces import ProtocolSettings
from smithy_core.aio.retries import StandardRetryStrategy
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import close
from smithy_core.auth import DefaultAuthResolver
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import Endpoint
from smithy_core.exceptions import CallError, DiscriminatorError, ModeledError
from smithy_core.interceptors import InterceptorChain
from smithy_core.interfaces import URI
from smithy_core.prelude import INTEGER, STRING
from smithy_core.retries import ExponentialRetryBackoffStrategy
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import RequestCompressionTrait, Trait
from smithy_core.types import TypedProperties
from smithy_http import Fields, tuples_to_fields
from smithy_http.aio import HTTPRequest, HTTPResponse
from smithy_http.compression import RequestCompression
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
    operation.input_stream_member = None
    return cast("APIOperation[Any, Any]", operation)


def _aws_json11_protocol() -> AwsJson11ClientProtocol:
    return AwsJson11ClientProtocol(
        ProtocolSettings(namespace="com.test", service_target="JsonService")
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


@pytest.mark.parametrize("kind", ["json", "query"])
@pytest.mark.parametrize("explicit", [None, "gzip"])
async def test_aws_protocol_compresses_serialized_request(
    kind: str, explicit: str | None
) -> None:
    protocol = (
        _aws_json11_protocol()
        if kind == "json"
        else AwsQueryClientProtocol(
            ProtocolSettings(
                namespace="com.test",
                service_target="QueryService",
                version="2020-01-08",
            )
        )
    )
    schema = Schema(
        id=ShapeID("com.test#TestOperation"),
        shape_type=ShapeType.OPERATION,
        traits=[RequestCompressionTrait({"encodings": ["gzip"]})],
    )
    operation = _mock_operation(schema)
    request = protocol.serialize_request(
        operation=operation,
        input=_TestInput(name="example"),
        endpoint=_URI(host="example.com"),
        context=TypedProperties(
            {
                "config": SimpleNamespace(
                    disable_request_compression=False,
                    request_min_compression_size_bytes=0
                    if explicit is None
                    else 10485760,
                    request_compression_encoding=explicit,
                )
            }
        ),
    )
    compressed = await request.consume_body_async()
    assert request.fields["content-encoding"].as_string() == "gzip"
    assert request.fields["content-length"].as_string() == str(len(compressed))
    expected = (
        b'{"name":"example"}'
        if kind == "json"
        else b"Action=TestOperation&Version=2020-01-08&name=example"
    )
    assert gzip.decompress(compressed) == expected


async def test_compressed_request_is_signed_and_replayed_by_pipeline() -> None:
    canonical_payloads: list[str] = []
    transmitted: list[bytes] = []

    class RecordingSigner(AsyncSigV4Signer):
        async def canonical_request(
            self, *, signing_properties: SigV4SigningProperties, request: AWSRequest
        ) -> str:
            canonical = await super().canonical_request(
                signing_properties=signing_properties, request=request
            )
            canonical_payloads.append(canonical.splitlines()[-1])
            return canonical

    class EndpointResolver:
        async def resolve_endpoint(self, params: Any) -> Endpoint:
            return Endpoint(uri=_URI(scheme="https", host="example.com"))

    class RetryTransport:
        TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = ()

        async def send(self, request: Any, **kwargs: Any) -> HTTPResponse:
            wire = await request.consume_body_async()
            transmitted.append(wire)
            assert request.fields["content-encoding"].as_string() == "gzip"
            assert "content-encoding" in request.fields["authorization"].as_string()
            assert int(request.fields["content-length"].as_string()) == len(wire)
            return HTTPResponse(
                status=429 if len(transmitted) == 1 else 200,
                fields=Fields(),
                body=b'{"__type":"ThrottlingException"}'
                if len(transmitted) == 1
                else b"{}",
            )

    scheme = SigV4AuthScheme(
        service="testservice", signer=cast(SigV4Signer, RecordingSigner())
    )
    config = SimpleNamespace(
        region="us-west-2",
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_session_token=None,
        aws_credentials_identity_resolver=StaticCredentialsResolver(
            AWSCredentialsIdentity(
                access_key_id="test-access-key", secret_access_key="test-secret-key"
            )
        ),
        disable_request_compression=False,
        request_min_compression_size_bytes=10240,
        request_compression_encoding="gzip",
    )
    operation = APIOperation(
        input=_TestInput,
        output=_EmptyOutput,
        static_schema=(
            ShapeType.OPERATION.value,
            "com.test",
            "TestOperation",
            {"smithy.api#requestCompression": {"encodings": ["gzip"]}},
            _INPUT_SCHEMA,
            _EMPTY_OUTPUT_SCHEMA,
            (),
        ),
        error_registry=TypeRegistry({}),
        effective_auth_schemes=[scheme.scheme_id],
    )
    call = ClientCall(
        input=_TestInput(name="example"),
        operation=operation,
        context=TypedProperties({"config": config}),
        interceptor=InterceptorChain([]),
        auth_scheme_resolver=DefaultAuthResolver(),
        supported_auth_schemes={scheme.scheme_id: scheme},
        endpoint_resolver=EndpointResolver(),
        retry_strategy=StandardRetryStrategy(
            max_attempts=2,
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=0),
        ),
    )
    output = await RequestPipeline(
        protocol=_aws_json11_protocol(), transport=RetryTransport()
    )(call)
    assert isinstance(output, _EmptyOutput)
    assert len(transmitted) == 2
    assert transmitted[0] == transmitted[1]
    assert gzip.decompress(transmitted[0]) == b'{"name":"example"}'
    assert canonical_payloads == [sha256(transmitted[0]).hexdigest()] * 2


async def test_signed_compressed_seekable_stream_is_not_fully_buffered() -> None:
    payload = b"".join(
        sha256(index.to_bytes(4, "big")).digest() for index in range(8192)
    )
    source = BytesIO(b"prefix" + payload)
    source.seek(6)
    fields = Fields()
    body = RequestCompression(encoding="gzip", minimum_size=0).compress(
        source, fields, streaming=True
    )
    assert isinstance(body, AsyncBytesReader)
    request = HTTPRequest(
        destination=_URI(scheme="https", host="example.com"),
        method="POST",
        fields=fields,
        body=body,
    )
    signed = await AsyncSigV4Signer().sign(
        request=cast(AWSRequest, request),
        identity=AWSCredentialsIdentity(
            access_key_id="test-key", secret_access_key="test-secret"
        ),
        properties={
            "region": "us-west-2",
            "service": "testservice",
            "payload_signing_enabled": True,
            "content_checksum_enabled": True,
        },
    )
    assert signed.body is body
    assert body.seekable()
    assert body.tell() == 0
    wire = await body.read()
    assert gzip.decompress(wire) == payload
    assert signed.fields["X-Amz-Content-SHA256"].as_string() == sha256(wire).hexdigest()
    await body.seek(0)
    assert await body.read() == wire
    await body.seek(17)
    assert body.tell() == 17
    assert await body.read(31) == wire[17:48]
    assert await body.seek(5, 1) == 53
    assert await body.read(3) == wire[53:56]
    assert await body.seek(-19, 2) == len(wire) - 19
    assert await body.read() == wire[-19:]
    assert await body.seek(len(wire) + 100) == len(wire)
    assert await body.read() == b""
    with pytest.raises(ValueError, match="Negative"):
        await body.seek(-1)
    with pytest.raises(ValueError, match="whence"):
        await body.seek(0, 99)
    await body.seek(0)
    assert await body.read() == wire
    await close(body)
    assert source.closed
    with pytest.raises(ValueError, match="closed"):
        await body.seek(0)


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

    # The message depends on which ijson backend is in use.
    with pytest.raises(
        IncompleteJSONError,
        match=r"premature EOF|parse error|Incomplete JSON content",
    ):
        await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry({}),
            context=TypedProperties(),
        )


async def test_aws_query_serializes_base_request_shape() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
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
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    with patch(
        "smithy_aws_core._private.query._xml.fromstring",
        wraps=ElementTree.fromstring,
    ) as parse:
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
    parse.assert_called_once()


async def test_aws_query_parses_success_body_once() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    operation = _mock_operation(_operation_schema("EmptyOperation"))
    cast(Any, operation).output = _EmptyOutput
    cast(Any, operation).output_schema = _EMPTY_OUTPUT_SCHEMA

    with patch(
        "smithy_aws_core._private.query._xml.fromstring",
        wraps=ElementTree.fromstring,
    ) as parse:
        output = await protocol.deserialize_response(
            operation=operation,
            request=cast(HTTPRequest, Mock()),
            response=HTTPResponse(
                status=200,
                fields=tuples_to_fields([]),
                body=b"<EmptyOperationResponse/>",
            ),
            error_registry=TypeRegistry({}),
            context=TypedProperties(),
        )

    assert isinstance(output, _EmptyOutput)
    parse.assert_called_once()


async def test_aws_query_resolves_modeled_error_from_default_namespace_fallback() -> (
    None
):
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
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
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
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


async def test_aws_query_parses_invalid_error_body_once() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )

    with patch(
        "smithy_aws_core._private.query._xml.fromstring",
        wraps=ElementTree.fromstring,
    ) as parse:
        with pytest.raises(CallError):
            await protocol.deserialize_response(
                operation=_mock_operation(_operation_schema("FailingOperation")),
                request=cast(HTTPRequest, Mock()),
                response=HTTPResponse(
                    status=500,
                    fields=tuples_to_fields([]),
                    body=b"not xml",
                ),
                error_registry=TypeRegistry({}),
                context=TypedProperties(),
            )

    parse.assert_called_once()


async def test_aws_query_reports_request_id_from_the_response_body() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    context = TypedProperties()
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields([]),
        body=(
            b"<ErrorResponse><Error><Code>InvalidAction</Code>"
            b"<message>bad request</message></Error>"
            b"<RequestId>body-request-id</RequestId></ErrorResponse>"
        ),
    )
    with pytest.raises(_ModeledQueryError):
        await protocol.deserialize_response(
            operation=_mock_operation(
                _operation_schema("FailingOperation"),
                error_schemas=[_INVALID_ACTION_ERROR_SCHEMA],
            ),
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#InvalidActionError"): _ModeledQueryError}
            ),
            context=context,
        )

    metadata = protocol.extract_response_metadata(response=response, context=context)
    assert metadata.request_id == "body-request-id"
    assert metadata.http_status_code == 400


async def test_aws_query_prefers_a_request_id_header_when_one_is_sent() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    context = TypedProperties()
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields([("x-amzn-requestid", "header-request-id")]),
        body=(
            b"<ErrorResponse><Error><Code>InvalidAction</Code>"
            b"<message>bad request</message></Error>"
            b"<RequestId>body-request-id</RequestId></ErrorResponse>"
        ),
    )
    await _deserialize_query_error(protocol, response, context)

    metadata = protocol.extract_response_metadata(response=response, context=context)
    assert metadata.request_id == "header-request-id"


async def test_aws_query_reports_no_request_id_when_the_body_has_none() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    response = HTTPResponse(
        status=200, fields=tuples_to_fields([]), body=b"<Response/>"
    )
    metadata = protocol.extract_response_metadata(
        response=response, context=TypedProperties()
    )
    assert metadata.request_id is None
    assert metadata.http_status_code == 200


async def test_aws_query_does_not_report_a_previous_attempts_request_id() -> None:
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    context = TypedProperties()

    first = HTTPResponse(
        status=400,
        fields=tuples_to_fields([]),
        body=(
            b"<ErrorResponse><Error><Code>InvalidAction</Code>"
            b"<message>throttled</message></Error>"
            b"<RequestId>attempt-1-id</RequestId></ErrorResponse>"
        ),
    )
    await _deserialize_query_error(protocol, first, context)
    assert (
        protocol.extract_response_metadata(response=first, context=context).request_id
        == "attempt-1-id"
    )

    second = HTTPResponse(
        status=400,
        fields=tuples_to_fields([]),
        body=(
            b"<ErrorResponse><Error><Code>InvalidAction</Code>"
            b"<message>bad request</message></Error></ErrorResponse>"
        ),
    )
    await _deserialize_query_error(protocol, second, context)

    metadata = protocol.extract_response_metadata(response=second, context=context)
    assert metadata.request_id is None


async def test_aws_query_does_not_report_a_previous_attempts_request_id_when_deserialization_is_skipped() -> (
    None
):
    protocol = AwsQueryClientProtocol(
        ProtocolSettings(
            namespace="com.test", service_target="QueryService", version="2020-01-08"
        )
    )
    context = TypedProperties()

    first = HTTPResponse(
        status=400,
        fields=tuples_to_fields([]),
        body=(
            b"<ErrorResponse><Error><Code>InvalidAction</Code>"
            b"<message>throttled</message></Error>"
            b"<RequestId>attempt-1-id</RequestId></ErrorResponse>"
        ),
    )
    await _deserialize_query_error(protocol, first, context)
    assert (
        protocol.extract_response_metadata(response=first, context=context).request_id
        == "attempt-1-id"
    )

    # A later attempt receives a response but never reaches deserialization (e.g. a
    # read_before_deserialization interceptor raises), so it records nothing. The ID
    # is bound to the first response, so this one's metadata must not borrow it.
    second = HTTPResponse(status=500, fields=tuples_to_fields([]), body=b"")

    metadata = protocol.extract_response_metadata(response=second, context=context)
    assert metadata.request_id is None


async def _deserialize_query_error(
    protocol: AwsQueryClientProtocol,
    response: HTTPResponse,
    context: TypedProperties,
) -> None:
    """Run an awsQuery error response through deserialization.

    Used to record whatever request ID the body carries the way a real call would,
    rather than reaching into the protocol's private storage key.
    """
    with pytest.raises(_ModeledQueryError):
        await protocol.deserialize_response(
            operation=_mock_operation(
                _operation_schema("FailingOperation"),
                error_schemas=[_INVALID_ACTION_ERROR_SCHEMA],
            ),
            request=cast(HTTPRequest, Mock()),
            response=response,
            error_registry=TypeRegistry(
                {ShapeID("com.test#InvalidActionError"): _ModeledQueryError}
            ),
            context=context,
        )


_NO_SUCH_BUCKET_SCHEMA = Schema.collection(
    id=ShapeID("com.test#NoSuchBucket"),
    traits=[Trait.new(id=ShapeID("smithy.api#error"), value="client")],
)


class _NoSuchBucket(ModeledError):
    """S3's NoSuchBucket error, which like every S3 error has no message member."""

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_NoSuchBucket":
        deserializer.read_struct(_NO_SUCH_BUCKET_SCHEMA, consumer=lambda _s, _de: None)
        return cls()


def _rest_xml_protocol() -> RestXmlClientProtocol:
    return RestXmlClientProtocol(
        ProtocolSettings(
            namespace="com.test",
            service_target="XmlService",
            xml_namespace="https://xml.example.com",
        )
    )


def _rest_xml_operation() -> APIOperation[Any, Any]:
    return APIOperation(
        input=_EmptyInput,
        output=_EmptyOutput,
        static_schema=(
            ShapeType.OPERATION.value,
            "com.test",
            "GetThing",
            {"smithy.api#http": {"method": "GET", "code": 200, "uri": "/"}},
            _EMPTY_INPUT_SCHEMA,
            _EMPTY_OUTPUT_SCHEMA,
            (_NO_SUCH_BUCKET_SCHEMA,),
        ),
        error_registry=TypeRegistry({}),
        effective_auth_schemes=[],
    )


async def test_rest_xml_modeled_error_falls_back_to_message_element() -> None:
    with patch(
        "smithy_aws_core._private.query._xml.fromstring",
        wraps=ElementTree.fromstring,
    ) as parse:
        with pytest.raises(_NoSuchBucket) as exc_info:
            await _rest_xml_protocol().deserialize_response(
                operation=_rest_xml_operation(),
                request=cast(HTTPRequest, Mock()),
                response=HTTPResponse(
                    status=404,
                    fields=tuples_to_fields([]),
                    body=(
                        b"<Error><Code>NoSuchBucket</Code>"
                        b"<Message>The specified bucket does not exist</Message></Error>"
                    ),
                ),
                error_registry=TypeRegistry(
                    {ShapeID("com.test#NoSuchBucket"): _NoSuchBucket}
                ),
                context=TypedProperties(),
            )

    assert exc_info.value.message == "The specified bucket does not exist"
    assert str(exc_info.value) == "The specified bucket does not exist"
    parse.assert_called_once()


_STATS_SCHEMA = Schema.collection(
    id=ShapeID("com.test#Stats"),
    members={"BytesScanned": {"target": INTEGER}},
)
_EVENTS_SCHEMA = Schema.collection(
    id=ShapeID("com.test#Events"),
    shape_type=ShapeType.UNION,
    members={"Stats": {"target": _STATS_SCHEMA}},
)


@dataclass
class _StatsEvent:
    bytes_scanned: int | None = None

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_StatsEvent":
        kwargs: dict[str, Any] = {}

        def _stats(schema: Schema, de: ShapeDeserializer) -> None:
            kwargs["bytes_scanned"] = de.read_integer(schema)

        deserializer.read_struct(
            _EVENTS_SCHEMA,
            consumer=lambda member, de: de.read_struct(member, consumer=_stats),
        )
        return cls(**kwargs)


async def test_rest_xml_receives_events_with_xml_payloads() -> None:
    message = EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": "Stats",
            ":content-type": "text/xml",
        },
        payload=b"<Stats><BytesScanned>512</BytesScanned></Stats>",
    )
    receiver = _rest_xml_protocol().create_event_receiver(
        operation=_rest_xml_operation(),
        request=cast(HTTPRequest, Mock()),
        response=HTTPResponse(
            status=200, fields=tuples_to_fields([]), body=message.encode()
        ),
        event_type=_StatsEvent,
        event_deserializer=_StatsEvent.deserialize,
        context=TypedProperties(),
    )

    assert await receiver.receive() == _StatsEvent(bytes_scanned=512)
