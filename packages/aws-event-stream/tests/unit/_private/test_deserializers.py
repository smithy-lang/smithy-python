# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from io import BytesIO
from typing import Any

import pytest
from aws_event_stream._private.deserializers import (
    AWSAsyncEventReceiver,
    EventDeserializer,
)
from aws_event_stream.events import Event, EventMessage
from aws_event_stream.exceptions import UnmodeledEventError
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.deserializers import DeserializeableShape
from smithy_json import JSONCodec

from . import (
    EVENT_STREAM_SERDE_CASES,
    INITIAL_REQUEST_CASE,
    INITIAL_RESPONSE_CASE,
    ErrorEvent,
    EventStreamDeserializer,
    EventStreamErrorEvent,
    EventStreamOperationInputOutput,
)


@pytest.mark.parametrize("expected,given", EVENT_STREAM_SERDE_CASES)
async def test_event_receiver(expected: DeserializeableShape, given: EventMessage):
    source = AsyncBytesReader(given.encode())
    deserializer = EventStreamDeserializer()
    receiver = AWSAsyncEventReceiver[Any](
        payload_codec=JSONCodec(), source=source, deserializer=deserializer.deserialize
    )

    result: Any = None

    try:
        result = await receiver.receive()
    except ErrorEvent as e:
        if isinstance(expected, EventStreamErrorEvent):
            expected = expected.value
        else:
            raise
        result = e

    assert result == expected


@pytest.mark.parametrize("expected,given", EVENT_STREAM_SERDE_CASES)
def test_event_deserializer(expected: DeserializeableShape, given: EventMessage):
    source = Event.decode(BytesIO(given.encode()))
    assert source is not None
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())
    result = EventStreamDeserializer().deserialize(deserializer)
    assert result == expected


def test_deserialize_initial_request():
    expected, given = INITIAL_REQUEST_CASE
    source = Event.decode(BytesIO(given.encode()))
    assert source is not None
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())
    result = EventStreamOperationInputOutput.deserialize(deserializer)
    assert result == expected


def test_deserialize_initial_response():
    expected, given = INITIAL_RESPONSE_CASE
    source = Event.decode(BytesIO(given.encode()))
    assert source is not None
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())
    result = EventStreamOperationInputOutput.deserialize(deserializer)
    assert result == expected


def test_deserialize_unmodeled_error():
    message = EventMessage(
        headers={
            ":message-type": "error",
            ":error-code": "InternalError",
            ":error-message": "An internal server error occurred.",
        }
    )
    source = Event.decode(BytesIO(message.encode()))
    assert source is not None
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())

    with pytest.raises(UnmodeledEventError, match="InternalError"):
        EventStreamOperationInputOutput.deserialize(deserializer)
