# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.serializers import SerializeableShape
from smithy_json import JSONCodec

from aws_event_stream._private.serializers import EventSerializer
from aws_event_stream.events import EventMessage

from . import EVENT_STREAM_SERDE_CASES, INITIAL_REQUEST_CASE, INITIAL_RESPONSE_CASE


@pytest.mark.parametrize("given,expected", EVENT_STREAM_SERDE_CASES)
def test_event_serializer_client_mode(
    given: SerializeableShape, expected: EventMessage
):
    serializer = EventSerializer(payload_codec=JSONCodec(), is_client_mode=True)
    given.serialize(serializer)
    actual = serializer.get_result()
    assert actual == expected


@pytest.mark.parametrize("given,expected", EVENT_STREAM_SERDE_CASES)
def test_event_serializer_server_mode(
    given: SerializeableShape, expected: EventMessage
):
    serializer = EventSerializer(payload_codec=JSONCodec(), is_client_mode=False)
    given.serialize(serializer)
    actual = serializer.get_result()
    assert actual == expected


def test_serialize_initial_request():
    test_event_serializer_client_mode(*INITIAL_REQUEST_CASE)


def test_serialize_initial_response():
    test_event_serializer_server_mode(*INITIAL_RESPONSE_CASE)
