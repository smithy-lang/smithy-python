# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Self, cast

import pytest
from smithy_core import URI
from smithy_core.aio.client import ClientCall, RequestPipeline
from smithy_core.aio.eventstream import DuplexEventStream, InputEventStream
from smithy_core.aio.interfaces import ClientProtocol, ClientTransport
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import EndpointResolverParams
from smithy_core.exceptions import UnsupportedTransportError
from smithy_core.interceptors import InterceptorChain
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import StreamingTrait
from smithy_core.types import TypedProperties

_STRING = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)

_EVENTS = Schema.collection(
    id=ShapeID("com.example#Events"),
    shape_type=ShapeType.UNION,
    members={"message": {"target": _STRING}},
)

_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.example#StreamingInput"),
    members={"events": {"target": _EVENTS, "traits": [StreamingTrait()]}},
)

_OUTPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.example#StreamingOutput"),
    members={"events": {"target": _EVENTS, "traits": [StreamingTrait()]}},
)


class _Input:
    def serialize(self, serializer: ShapeSerializer) -> None:
        pass


class _Output:
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls()


class _Event:
    def serialize(self, serializer: ShapeSerializer) -> None:
        pass

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls()


_OPERATION = APIOperation(
    input=_Input,
    output=_Output,
    schema=Schema(
        id=ShapeID("com.example#StreamingOperation"),
        shape_type=ShapeType.OPERATION,
    ),
    input_schema=_INPUT_SCHEMA,
    output_schema=_OUTPUT_SCHEMA,
    error_registry=TypeRegistry({}),
    effective_auth_schemes=[],
    error_schemas=[],
)


class _StubRequest:
    def __init__(self) -> None:
        self.destination = URI(host="example.com")
        self.body = b""

    async def consume_body_async(self) -> bytes:
        return b""

    def consume_body(self) -> bytes:
        return b""


class _StubResponse:
    body = b""

    async def consume_body_async(self) -> bytes:
        return b""

    def consume_body(self) -> bytes:
        return b""


class _StubEventPublisher:
    async def send(self, event: Any) -> None:
        pass

    async def close(self) -> None:
        pass


class _StubEventReceiver:
    async def receive(self) -> Any:
        return None

    async def close(self) -> None:
        pass


class _StubProtocol:
    @property
    def id(self) -> ShapeID:
        return ShapeID("com.example#testProtocol")

    def serialize_request(self, **kwargs: Any) -> _StubRequest:
        return _StubRequest()

    def set_service_endpoint(self, *, request: Any, endpoint: Any) -> Any:
        return request

    async def deserialize_response(self, **kwargs: Any) -> _Output:
        return _Output()

    def create_event_publisher(self, **kwargs: Any) -> _StubEventPublisher:
        return _StubEventPublisher()

    def create_event_receiver(self, **kwargs: Any) -> _StubEventReceiver:
        return _StubEventReceiver()


class _StubEndpoint:
    def __init__(self) -> None:
        self.uri = URI(host="example.com")
        self.properties = TypedProperties()


class _StubEndpointResolver:
    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> Any:
        return _StubEndpoint()


class _StubAuthResolver:
    def resolve_auth_scheme(self, *, auth_parameters: Any) -> list[Any]:
        return []


class _UndeclaredTransport:
    """A transport that does not declare whether it supports duplex streaming."""

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = ()

    async def send(self, request: Any) -> _StubResponse:
        return _StubResponse()


class _NonDuplexTransport(_UndeclaredTransport):
    SUPPORTS_DUPLEX_STREAMING = False


class _DuplexTransport(_UndeclaredTransport):
    SUPPORTS_DUPLEX_STREAMING = True


def _pipeline(transport: object) -> RequestPipeline[Any, Any]:
    # The stubs are intentionally structural (they don't subclass the
    # protocols), so cast them to keep the type checker focused on the
    # runtime behavior under test.
    return RequestPipeline(
        protocol=cast("ClientProtocol[Any, Any]", _StubProtocol()),
        transport=cast("ClientTransport[Any, Any]", transport),
    )


def _client_call() -> ClientCall[Any, Any]:
    return ClientCall(
        input=_Input(),
        operation=_OPERATION,
        context=TypedProperties(),
        interceptor=InterceptorChain([]),
        auth_scheme_resolver=_StubAuthResolver(),
        supported_auth_schemes={},
        endpoint_resolver=_StubEndpointResolver(),
        retry_strategy=None,  # type: ignore[arg-type] # unused for streaming input
    )


async def test_duplex_stream_raises_for_undeclared_transport() -> None:
    pipeline = _pipeline(_UndeclaredTransport())

    with pytest.raises(UnsupportedTransportError) as exc_info:
        await pipeline.duplex_stream(_client_call(), _Event, _Event, _Event.deserialize)

    assert "_UndeclaredTransport" in str(exc_info.value)
    assert "com.example#StreamingOperation" in str(exc_info.value)


async def test_duplex_stream_raises_for_non_duplex_transport() -> None:
    pipeline = _pipeline(_NonDuplexTransport())

    with pytest.raises(UnsupportedTransportError):
        await pipeline.duplex_stream(_client_call(), _Event, _Event, _Event.deserialize)


async def test_duplex_stream_proceeds_for_duplex_transport() -> None:
    pipeline = _pipeline(_DuplexTransport())

    stream = await pipeline.duplex_stream(
        _client_call(), _Event, _Event, _Event.deserialize
    )

    assert isinstance(stream, DuplexEventStream)
    output, output_stream = await stream.await_output()
    assert isinstance(output, _Output)
    assert isinstance(output_stream, _StubEventReceiver)


async def test_input_stream_does_not_require_duplex_support() -> None:
    pipeline = _pipeline(_NonDuplexTransport())

    stream = await pipeline.input_stream(_client_call(), _Event)

    assert isinstance(stream, InputEventStream)
    assert isinstance(await stream.await_output(), _Output)
