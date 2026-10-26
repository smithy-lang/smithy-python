#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Publisher behavior for the initial-request event.

The initial-request must be the first frame on the wire and, when signing is
configured, the first event signed -- it seeds the event signature chain off the
request signature, so a user event must never precede or outrank it.
"""

from io import BytesIO
from typing import Any

import pytest
from smithy_aws_event_stream._private.serializers import EventSerializer
from smithy_aws_event_stream.aio import AWSEventPublisher, SigningConfig
from smithy_aws_event_stream.events import Event, EventMessage
from smithy_json import JSONCodec

from .._private import (
    EventStreamMessageEvent,
    EventStreamOperationInputOutput,
    MessageEvent,
)


class _CollectingWriter:
    def __init__(self) -> None:
        self.frames: list[bytes] = []

    async def write(self, data: bytes) -> None:
        self.frames.append(data)


def _event_types(frames: list[bytes]) -> list[str]:
    out: list[str] = []
    for frame in frames:
        event = Event.decode(BytesIO(frame))
        assert event is not None
        out.append(str(event.message.headers.get(":event-type")))
    return out


def _initial() -> EventMessage:
    serializer = EventSerializer(payload_codec=JSONCodec(), is_client_mode=True)
    EventStreamOperationInputOutput(message="init").serialize(serializer)
    result = serializer.get_result()
    assert result is not None
    return result


def _user_event() -> EventStreamMessageEvent:
    return EventStreamMessageEvent(value=MessageEvent(body_member="one"))


def _publisher(writer: _CollectingWriter, **kwargs: Any) -> AWSEventPublisher[Any]:
    return AWSEventPublisher[Any](
        payload_codec=JSONCodec(),
        async_writer=writer,
        initial_message=_initial(),
        **kwargs,
    )


async def test_prepare_writes_initial_request_first() -> None:
    writer = _CollectingWriter()
    publisher = _publisher(writer)

    await publisher.prepare()
    await publisher.send(_user_event())

    assert _event_types(writer.frames) == ["initial-request", "message"]


async def test_initial_request_flushed_before_first_send_without_prepare() -> None:
    # Even if the caller skips prepare(), the first send() must not jump the queue.
    writer = _CollectingWriter()
    publisher = _publisher(writer)

    await publisher.send(_user_event())

    assert _event_types(writer.frames) == ["initial-request", "message"]


async def test_initial_request_is_signed_first() -> None:
    signed_order: list[str] = []

    class _RecordingSigner:
        async def sign(
            self, *, event: EventMessage, identity: Any, properties: Any
        ) -> EventMessage:
            signed_order.append(str(event.headers.get(":event-type")))
            return event

        async def sign_empty(
            self, *, event: EventMessage, identity: Any, properties: Any
        ) -> EventMessage:
            signed_order.append("<empty>")
            return event

    class _StubResolver:
        async def get_identity(self, *, properties: Any) -> Any:
            return object()

    signing_config = SigningConfig(
        signer=_RecordingSigner(),  # type: ignore[arg-type]
        signing_properties={},  # type: ignore[arg-type]
        identity_resolver=_StubResolver(),  # type: ignore[arg-type]
        identity_properties={},  # type: ignore[arg-type]
    )

    writer = _CollectingWriter()
    publisher = _publisher(writer, signing_config=signing_config)

    await publisher.send(_user_event())
    await publisher.close()

    # Chain order: initial-request signed first, then the user event, then the empty
    # terminating frame.
    assert signed_order == ["initial-request", "message", "<empty>"]


async def test_write_failure_aborts_without_reflushing() -> None:
    # A failed write must abort: close the underlying writer and mark the publisher
    # closed, NOT route through close() (which would re-flush the pending initial frame
    # onto the dead writer and attempt a terminator).
    class _FailingWriter:
        def __init__(self) -> None:
            self.frames: list[bytes] = []
            self.closed = False

        async def write(self, data: bytes) -> None:
            raise OSError("socket is down")

        async def close(self) -> None:
            self.closed = True

    writer = _FailingWriter()
    publisher = _publisher(writer)  # type: ignore[arg-type]

    with pytest.raises(OSError, match=r"Failed to write to stream\."):
        await publisher.send(_user_event())

    assert writer.frames == []  # nothing reached the wire
    assert writer.closed is True  # underlying writer torn down
    assert publisher.closed is True  # subsequent send/close no-op
