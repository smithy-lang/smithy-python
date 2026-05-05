# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock

import pytest
from smithy_aws_event_stream._private.serializers import EventSerializer
from smithy_aws_event_stream.aio import AWSEventPublisher
from smithy_aws_event_stream.events import Event, EventMessage
from smithy_core.aio.types import AsyncBytesProvider
from smithy_core.serializers import SerializeableShape
from smithy_json import JSONCodec

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


async def test_publisher_closes_reader():
    writer = AsyncBytesProvider()
    publisher: AWSEventPublisher[Any] = AWSEventPublisher(
        payload_codec=JSONCodec(), async_writer=writer
    )

    assert not publisher.closed
    assert not writer.closed
    await publisher.close()
    assert publisher.closed
    assert writer.closed


async def test_send_after_close():
    writer = AsyncBytesProvider()
    publisher: AWSEventPublisher[Any] = AWSEventPublisher(
        payload_codec=JSONCodec(), async_writer=writer
    )

    await publisher.close()
    assert publisher.closed
    with pytest.raises(IOError):
        await publisher.send(EVENT_STREAM_SERDE_CASES[0][0])


async def test_send_to_closed_writer():
    writer = AsyncBytesProvider()
    publisher: AWSEventPublisher[Any] = AWSEventPublisher(
        payload_codec=JSONCodec(), async_writer=writer
    )

    await writer.close()
    with pytest.raises(IOError):
        await publisher.send(EVENT_STREAM_SERDE_CASES[0][0])

    assert publisher.closed


async def test_close_sends_empty_end_frame_when_signing():
    writer = AsyncBytesProvider()
    end_frame = EventMessage()
    signing_config = AsyncMock()
    signing_config.signer.sign_empty.return_value = end_frame

    publisher: AWSEventPublisher[Any] = AWSEventPublisher(
        payload_codec=JSONCodec(), async_writer=writer, signing_config=signing_config
    )

    # Read from the writer concurrently with close(), since close() flushes
    # and blocks until all chunks are consumed.
    reader = asyncio.create_task(_read(writer))
    await publisher.close()
    written = await reader

    signing_config.signer.sign_empty.assert_awaited_once()
    assert publisher.closed
    assert writer.closed

    decoded = Event.decode(BytesIO(written))
    assert decoded is not None
    assert decoded.message.payload == b""
    assert decoded.message.headers == {}


async def _read(source: AsyncBytesProvider) -> bytes:
    return b"".join([chunk async for chunk in source])
