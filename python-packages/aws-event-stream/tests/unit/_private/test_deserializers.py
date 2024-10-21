# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from io import BytesIO

import pytest
from smithy_core.deserializers import DeserializeableShape
from smithy_json import JSONCodec

from aws_event_stream._private.deserializers import EventDeserializer
from aws_event_stream.events import Event, EventMessage
from aws_event_stream.exceptions import UnmodeledEventError

from . import (
    EVENT_STREAM_SERDE_CASES,
    INITIAL_REQUEST_CASE,
    INITIAL_RESPONSE_CASE,
    EventStreamDeserializer,
    EventStreamOperationInputOutput,
)


@pytest.mark.parametrize("expected,given", EVENT_STREAM_SERDE_CASES)
def test_event_deserializer(expected: DeserializeableShape, given: EventMessage):
    source = Event.decode(BytesIO(given.encode()))
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())
    result = EventStreamDeserializer().deserialize(deserializer)
    assert result == expected


def test_deserialize_initial_request():
    expected, given = INITIAL_REQUEST_CASE
    source = Event.decode(BytesIO(given.encode()))
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())
    result = EventStreamOperationInputOutput.deserialize(deserializer)
    assert result == expected


def test_deserialize_initial_response():
    expected, given = INITIAL_RESPONSE_CASE
    source = Event.decode(BytesIO(given.encode()))
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
    deserializer = EventDeserializer(event=source, payload_codec=JSONCodec())

    with pytest.raises(UnmodeledEventError, match="InternalError"):
        EventStreamOperationInputOutput.deserialize(deserializer)
