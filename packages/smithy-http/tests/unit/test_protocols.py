#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Self

import pytest
from smithy_core import URI
from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import Endpoint
from smithy_core.exceptions import CallError, ModeledError
from smithy_core.interfaces import TypedProperties as TypedPropertiesInterface
from smithy_core.interfaces import URI as URIInterface
from smithy_core.program import Program, run_program
from smithy_core.retries import RETRY_ATTEMPT, RETRY_STRATEGY
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import HTTPPayloadTrait, StreamingTrait
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields, HTTPRequest, HTTPResponse
from smithy_http.interfaces import HTTPErrorIdentifier
from smithy_http.interfaces import HTTPRequest as HTTPRequestInterface
from smithy_http.interfaces import HTTPResponse as HTTPResponseInterface
from smithy_http.protocols import HttpBindingClientProtocol, HttpClientProtocol
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

    def deserialize_response_program(self, **kwargs: Any) -> Program[Any]:
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


class StreamingOutput(MockOutput):
    SCHEMA = Schema.collection(
        id=ShapeID("ns.foo#StreamingOutput"),
        members={
            "payload": {
                "target": Schema(
                    id=ShapeID("ns.foo#StreamingBlob"),
                    shape_type=ShapeType.BLOB,
                    traits=[StreamingTrait()],
                ),
                "traits": [HTTPPayloadTrait()],
            }
        },
    )


class _StubRegistry:
    def __init__(self, classes: dict[str, type]) -> None:
        self._classes = classes

    def build(self, name: str) -> type:
        return self._classes[name]


_STUB_REGISTRY = _StubRegistry(
    {
        "LegacyInput": LegacyInput,
        "StructInput": StructInput,
        "MockOutput": MockOutput,
        "StreamingOutput": StreamingOutput,
    }
)


def test_http_binding_protocol_falls_back_to_legacy_serialize() -> None:
    operation: APIOperation[Any, Any] = APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            "ns.foo",
            "LegacyOperation",
            {"smithy.api#http": {"method": "POST", "code": 200, "uri": "/legacy"}},
            LegacyInput.SCHEMA,
            MockOutput.SCHEMA,
            (),
        ),
        model_registry=_STUB_REGISTRY,
        effective_auth_schemes=[],
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
    operation: APIOperation[Any, Any] = APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            "ns.foo",
            "StructOperation",
            {"smithy.api#http": {"method": "POST", "code": 200, "uri": "/structure"}},
            StructInput.SCHEMA,
            MockOutput.SCHEMA,
            (),
        ),
        model_registry=_STUB_REGISTRY,
        effective_auth_schemes=[],
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
    ("output", "expected_reads"),
    [(MockOutput, 1), (StreamingOutput, 0)],
)
def test_deserialize_response_uses_cached_streaming_member(
    monkeypatch: pytest.MonkeyPatch,
    output: type[MockOutput],
    expected_reads: int,
) -> None:
    def fail_if_scanned(_: APIOperation[Any, Any]) -> None:
        pytest.fail("output_stream_member should not be scanned")

    monkeypatch.setattr(
        APIOperation,
        "output_stream_member",
        property(fail_if_scanned),
    )
    operation: APIOperation[Any, Any] = APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            "ns.foo",
            "DeserializeOperation",
            {"smithy.api#http": {"method": "GET", "code": 200, "uri": "/"}},
            LegacyInput.SCHEMA,
            output.SCHEMA,
            (),
        ),
        model_registry=_STUB_REGISTRY,
        effective_auth_schemes=[],
    )
    request = HTTPRequest(
        destination=URI(host="example.com"),
        method="GET",
        fields=Fields(),
    )
    response = HTTPResponse(body=b"{}", status=200, fields=Fields())
    reads: list[Any] = []

    def read_body(body: Any) -> bytes:
        reads.append(body)
        return body

    run_program(
        MockBindingProtocol().deserialize_response_program(
            operation=operation,
            request=request,
            response=response,
            error_registry=TypeRegistry({}),
            context=TypedProperties(),
            read_body=read_body,
        )
    )

    assert len(reads) == expected_reads


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


def test_extract_response_metadata_reports_only_the_status_code() -> None:
    # Request Ids are not an HTTP concept. The base HTTP layer must not read
    # request IDs even when an AWS-style header is present; that knowledge
    # belongs in smithy-aws-core.
    response = HTTPResponse(
        status=429,
        fields=Fields([Field(name="x-amzn-requestid", values=["rid"])]),
    )

    metadata = MockProtocol().extract_response_metadata(
        response=response, context=TypedProperties()
    )

    assert metadata.http_status_code == 429
    assert metadata.request_id is None
    assert metadata.extended_request_id is None


def _attempt_request() -> HTTPRequest:
    return HTTPRequest(
        method="POST", destination=URI(host="example.com"), fields=Fields()
    )


def _attempt_context(*, sends: bool = True) -> TypedProperties:
    return TypedProperties({"config": SimpleNamespace(_sends_retry_info_headers=sends)})


def _prepare(context: TypedProperties) -> HTTPRequestInterface:
    return MockProtocol().prepare_attempt_request(
        request=_attempt_request(), context=context
    )


@pytest.mark.parametrize(
    "context",
    [
        TypedProperties(),
        TypedProperties({"config": SimpleNamespace()}),
        _attempt_context(sends=False),
    ],
    ids=["no config", "no flag", "flag off"],
)
def test_prepare_attempt_request_adds_nothing_without_the_flag(
    context: TypedProperties,
) -> None:
    request = _prepare(context)
    assert "amz-sdk-invocation-id" not in request.fields
    assert "amz-sdk-request" not in request.fields


def test_invocation_id_is_a_version_4_uuid() -> None:
    request = _prepare(_attempt_context())
    assert uuid.UUID(request.fields["amz-sdk-invocation-id"].as_string()).version == 4


def test_invocation_id_is_the_same_on_every_attempt() -> None:
    context = _attempt_context()
    ids: set[str] = set()
    for attempt in range(1, 4):
        context[RETRY_ATTEMPT] = attempt
        ids.add(_prepare(context).fields["amz-sdk-invocation-id"].as_string())
    assert len(ids) == 1


def test_invocation_id_differs_between_calls() -> None:
    first = _prepare(_attempt_context()).fields["amz-sdk-invocation-id"].as_string()
    second = _prepare(_attempt_context()).fields["amz-sdk-invocation-id"].as_string()
    assert first != second


def test_retry_headers_replace_a_callers_values() -> None:
    request = _attempt_request()
    request.fields.set_field(Field(name="amz-sdk-invocation-id", values=["caller"]))
    request.fields.set_field(Field(name="amz-sdk-request", values=["caller"]))
    prepared = MockProtocol().prepare_attempt_request(
        request=request, context=_attempt_context()
    )
    invocation_id = prepared.fields["amz-sdk-invocation-id"].as_string()
    assert uuid.UUID(invocation_id).version == 4
    assert prepared.fields["amz-sdk-request"].as_string() == "attempt=1"


_NO_STRATEGY = object()


def _request_header(strategy: Any, attempt: int | None = None) -> str:
    context = _attempt_context()
    if strategy is not _NO_STRATEGY:
        context[RETRY_STRATEGY] = strategy
    if attempt is not None:
        context[RETRY_ATTEMPT] = attempt
    return _prepare(context).fields["amz-sdk-request"].as_string()


@pytest.mark.parametrize(
    "strategy",
    [
        _NO_STRATEGY,
        SimpleNamespace(),
        SimpleNamespace(max_attempts=None),
        SimpleNamespace(max_attempts=0),
        SimpleNamespace(max_attempts=True),
    ],
    ids=["no strategy", "no attribute", "None", "0", "True"],
)
def test_request_header_omits_unknown_max(strategy: Any) -> None:
    assert _request_header(strategy) == "attempt=1"


def test_request_header_sends_the_attempt_and_max_attempts() -> None:
    assert _request_header(SimpleNamespace(max_attempts=3), 2) == "attempt=2; max=3"


_MODELED_ERROR_ID = ShapeID("ns.foo#ModeledError")


class _ModeledErrorIdentifier(HTTPErrorIdentifier):
    def identify(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponseInterface,
    ) -> ShapeID | None:
        return _MODELED_ERROR_ID


class _ModeledErrorProtocol(MockBindingProtocol):
    _error_identifier = _ModeledErrorIdentifier()


class _ModeledError(ModeledError):
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls("modeled error")


@dataclass(kw_only=True)
class _NotRetrySafeError(ModeledError):
    is_retry_safe: bool | None = False

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls("not retry safe")


def _deserialize_error(
    protocol: HttpBindingClientProtocol, status: int, error_registry: TypeRegistry
) -> CallError:
    operation: APIOperation[Any, Any] = APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            "ns.foo",
            "FailingOperation",
            {"smithy.api#http": {"method": "GET", "code": 200, "uri": "/"}},
            LegacyInput.SCHEMA,
            MockOutput.SCHEMA,
            (),
        ),
        model_registry=_STUB_REGISTRY,
        effective_auth_schemes=[],
    )
    with pytest.raises(CallError) as exc_info:
        run_program(
            protocol.deserialize_response_program(
                operation=operation,
                request=HTTPRequest(
                    destination=URI(host="example.com"),
                    method="GET",
                    fields=Fields(),
                ),
                response=HTTPResponse(body=b"", status=status, fields=Fields()),
                error_registry=error_registry,
                context=TypedProperties(),
                read_body=lambda body: body,
            )
        )
    return exc_info.value


@pytest.mark.parametrize(
    "status, error_shape, expected",
    [
        (500, _ModeledError, True),
        (400, _ModeledError, None),
        (503, _NotRetrySafeError, False),
    ],
)
def test_http_binding_modeled_error_retry_safety(
    status: int,
    error_shape: type[_ModeledError | _NotRetrySafeError],
    expected: bool | None,
) -> None:
    error = _deserialize_error(
        _ModeledErrorProtocol(), status, TypeRegistry({_MODELED_ERROR_ID: error_shape})
    )

    assert isinstance(error, error_shape)
    assert error.is_retry_safe is expected
