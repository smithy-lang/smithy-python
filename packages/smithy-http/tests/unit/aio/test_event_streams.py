#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end event-stream wiring for the RPC protocols (rpcv2Cbor).

Exercises the two halves the RPC protocols add over the shared factory: the
``initial-request`` frame written into a writable request body, and the
``initial-response`` peel that feeds the stream's initial output before the event
receiver continues from the same reader.
"""

from io import BytesIO
from typing import Any

import pytest
from smithy_core import URI
from smithy_core.aio.interfaces import AsyncWriter, ProtocolSettings
from smithy_core.aio.types import AsyncBytesProvider, AsyncBytesReader
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.prelude import STRING
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import StreamingTrait
from smithy_core.types import TypedProperties
from smithy_http import Fields
from smithy_http.aio import HTTPRequest, HTTPResponse
from smithy_http.aio.protocols import RpcV2CborClientProtocol

pytest.importorskip("smithy_cbor")

from smithy_aws_event_stream.aio import AWSEventReceiver
from smithy_aws_event_stream.events import Event, EventMessage
from smithy_cbor import CBORCodec

_CODEC = CBORCodec()

_MESSAGE_EVENT = Schema.collection(
    id=ShapeID("smithy.example#MessageEvent"),
    members={"body": {"target": STRING}},
)

_EVENT_STREAM = Schema.collection(
    id=ShapeID("smithy.example#EventStream"),
    shape_type=ShapeType.UNION,
    traits=[StreamingTrait()],
    members={"message": {"target": _MESSAGE_EVENT}},
)


class InitialMessage:
    """The operation input/output; ``message`` is the initial payload."""

    def __init__(self, message: str | None = None) -> None:
        self.message = message

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(_STREAM_IO_SCHEMA) as s:
            if self.message is not None:
                s.write_string(_STREAM_IO_SCHEMA.members["message"], self.message)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "InitialMessage":
        instance = cls()

        def _consume(schema: Schema, de: ShapeDeserializer) -> None:
            instance.message = de.read_string(_STREAM_IO_SCHEMA.members["message"])

        deserializer.read_struct(_STREAM_IO_SCHEMA, _consume)
        return instance


class _MessageEvent:
    def __init__(self, body: str | None = None) -> None:
        self.body = body

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(_MESSAGE_EVENT) as s:
            if self.body is not None:
                s.write_string(_MESSAGE_EVENT.members["body"], self.body)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_MessageEvent":
        instance = cls()

        def _consume(schema: Schema, de: ShapeDeserializer) -> None:
            instance.body = de.read_string(_MESSAGE_EVENT.members["body"])

        deserializer.read_struct(_MESSAGE_EVENT, _consume)
        return instance


# The event-stream member is NOT part of the operation IO schema in codegen, but the
# protocol detects streaming via input_stream_member/output_stream_member, which scans
# the schema members for a @streaming target. So the IO schema used by the operation
# carries the stream member here.
_STREAM_IO_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StreamOpIO"),
    members={
        "message": {"target": STRING},
        "stream": {"target": _EVENT_STREAM},
    },
)


class _StubRegistry:
    def build(self, name: str) -> type:
        return InitialMessage


def _operation() -> APIOperation[Any, Any]:
    return APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            "smithy.example",
            "StreamOp",
            {},
            _STREAM_IO_SCHEMA,
            _STREAM_IO_SCHEMA,
            (),
        ),
        model_registry=_StubRegistry(),
        effective_auth_schemes=[],
    )


def _message_event_deserializer(deserializer: ShapeDeserializer) -> _MessageEvent:
    """Union deserializer: dispatch the event-stream union to its member event."""
    result: _MessageEvent | None = None

    def _consume(schema: Schema, de: ShapeDeserializer) -> None:
        nonlocal result
        if schema.expect_member_index() == 0:
            result = _MessageEvent.deserialize(de)

    deserializer.read_struct(_EVENT_STREAM, _consume)
    if result is None:
        raise AssertionError("expected a message event")
    return result


def _protocol() -> RpcV2CborClientProtocol:
    return RpcV2CborClientProtocol(
        ProtocolSettings(namespace="smithy.example", service_target="StreamService")
    )


def _request() -> HTTPRequest:
    return HTTPRequest(
        destination=URI(host="example.com"), method="POST", fields=Fields()
    )


async def test_serialize_request_writes_initial_request_frame() -> None:
    request = _protocol().serialize_request(
        operation=_operation(),
        input=InitialMessage(message="hello"),
        endpoint=URI(host="example.com"),
        context=TypedProperties(),
    )

    assert (
        request.fields["Content-Type"].as_string()
        == "application/vnd.amazon.eventstream"
    )
    body = request.body
    assert isinstance(body, AsyncBytesProvider)
    assert isinstance(body, AsyncWriter)

    frame_bytes = await anext(aiter(body))
    event = Event.decode(BytesIO(frame_bytes))
    assert event is not None
    assert event.message.headers[":message-type"] == "event"
    assert event.message.headers[":event-type"] == "initial-request"
    decoded = _CODEC.deserialize(source=event.message.payload, shape=InitialMessage)
    assert decoded.message == "hello"


async def test_deserialize_response_peels_initial_response_then_streams() -> None:
    operation = _operation()
    initial = EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": "initial-response",
            ":content-type": "application/cbor",
        },
        payload=_CODEC.serialize(shape=InitialMessage(message="the initial response")),
    )
    event = EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": "message",
            ":content-type": "application/cbor",
        },
        payload=_CODEC.serialize(shape=_MessageEvent("first event")),
    )
    response = HTTPResponse(
        status=200,
        fields=Fields(),
        body=AsyncBytesReader(initial.encode() + event.encode()),
    )

    context = TypedProperties()
    output = await _protocol().deserialize_response(
        operation=operation,
        request=_request(),
        response=response,
        error_registry=TypeRegistry({}),
        context=context,
    )

    assert isinstance(output, InitialMessage)
    assert output.message == "the initial response"

    receiver = _protocol().create_event_receiver(
        operation=operation,
        request=_request(),
        response=response,
        event_type=Any,
        event_deserializer=_message_event_deserializer,
        context=context,
    )
    assert isinstance(receiver, AWSEventReceiver)
    received = await receiver.receive()
    assert received is not None
    assert received.body == "first event"
