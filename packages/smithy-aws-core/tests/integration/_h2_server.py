#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""A localhost HTTP/2 server harness for driving generated clients over a real
bidirectional transport. Test-runtime concerns (which client, which shapes, what
to assert) live in the test modules that use this harness."""

import asyncio
import ssl
from collections.abc import Awaitable, Callable
from io import BytesIO

import h2.config
import h2.connection
import h2.events
import trustme
from smithy_aws_event_stream.events import Event, EventMessage

EVENT_STREAM_CONTENT_TYPE = "application/vnd.amazon.eventstream"
# The defaults speak rpcv2Cbor; pass ``payload_content_type`` / ``smithy_protocol``
# to H2BidiServer to speak another rpcv2 protocol (e.g. rpcv2Json).
CBOR_CONTENT_TYPE = "application/cbor"
# rpcv2 responses must echo the request's Smithy-Protocol header; clients treat a
# response without it as malformed.
SMITHY_PROTOCOL = "rpc-v2-cbor"


def encode_event(
    event_type: str, payload: bytes, content_type: str = CBOR_CONTENT_TYPE
) -> bytes:
    return EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": event_type,
            ":content-type": content_type,
        },
        payload=payload,
    ).encode()


# A referee drives the turn-based exchange. It is called once with ``None`` to open
# the game (after the client's initial-request lands), then once per subsequent client
# event frame. It sends server frames through the ServerStream and returns True when
# the game is over.
Referee = Callable[["Event | None", "ServerStream"], Awaitable[bool]]


class ServerStream:
    """The server's writable side of one event stream, handed to the referee."""

    def __init__(
        self,
        conn: h2.connection.H2Connection,
        stream_id: int,
        content_type: str = CBOR_CONTENT_TYPE,
    ) -> None:
        self._conn = conn
        self._stream_id = stream_id
        self._content_type = content_type

    def send(self, event_type: str, payload: bytes) -> None:
        self._conn.send_data(
            self._stream_id,
            encode_event(event_type, payload, self._content_type),
            end_stream=False,
        )

    def end(self) -> None:
        self._conn.send_data(self._stream_id, b"", end_stream=True)


class H2BidiServer:
    """A localhost HTTP/2 server that runs a referee over one duplex event stream.

    After the client's ``initial-request`` arrives, the referee is opened (``None``)
    and thereafter handed each client event frame, deciding what to send back. The
    ``initial-request`` itself is recorded in ``received_event_types`` but not passed
    to the referee -- it is request setup, not a game move. ``received_event_types``
    records every client frame's ``:event-type`` for post-hoc assertions, and
    ``received_content_types`` its ``:content-type``.

    ``payload_content_type`` is the ``:content-type`` of the event frames the server
    sends, and ``smithy_protocol`` the ``Smithy-Protocol`` response header value; both
    default to rpcv2Cbor.
    """

    def __init__(
        self,
        referee: Referee,
        *,
        payload_content_type: str = CBOR_CONTENT_TYPE,
        smithy_protocol: str = SMITHY_PROTOCOL,
    ) -> None:
        self._referee = referee
        self._payload_content_type = payload_content_type
        self._smithy_protocol = smithy_protocol
        self._ca = trustme.CA()
        self._server_cert = self._ca.issue_cert("localhost", "127.0.0.1")
        self._ca_cert_ctx = self._ca.cert_pem.tempfile()
        self.ca_cert_path = self._ca_cert_ctx.__enter__()
        self.host = "127.0.0.1"
        self.port = 0
        self._server: asyncio.base_events.Server | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self.received_event_types: list[str] = []
        self.received_content_types: list[str] = []

    async def __aenter__(self) -> "H2BidiServer":
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.set_alpn_protocols(["h2"])
        self._server_cert.configure_cert(ssl_context)
        self._server = await asyncio.start_server(
            self._track, self.host, 0, ssl=ssl_context
        )
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc: object) -> None:
        for task in self._tasks:
            task.cancel()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        self._ca_cert_ctx.__exit__(None, None, None)

    def _track(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        task = asyncio.ensure_future(self._handle(reader, writer))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        conn = h2.connection.H2Connection(
            config=h2.config.H2Configuration(client_side=False)
        )
        conn.initiate_connection()
        writer.write(conn.data_to_send())
        await writer.drain()

        decoder = _FrameDecoder()
        stream: ServerStream | None = None
        done = False
        client_ended = False

        try:
            # Keep the connection up after the game ends until the client half-closes
            # its side, so the client's own end-of-stream lands on a live stream.
            while not writer.is_closing() and not (done and client_ended):
                data = await reader.read(65536)
                if not data:
                    break
                for h2_event in conn.receive_data(data):
                    if isinstance(h2_event, h2.events.RequestReceived):
                        stream = ServerStream(
                            conn, h2_event.stream_id, self._payload_content_type
                        )
                        self._respond_headers(conn, stream)
                    elif isinstance(h2_event, h2.events.StreamEnded):
                        client_ended = True
                    elif isinstance(h2_event, h2.events.DataReceived):
                        conn.acknowledge_received_data(
                            len(h2_event.data), h2_event.stream_id
                        )
                        if stream is None or done:
                            continue
                        for frame in decoder.feed(h2_event.data):
                            event_type = str(frame.message.headers.get(":event-type"))
                            self.received_event_types.append(event_type)
                            self.received_content_types.append(
                                str(frame.message.headers.get(":content-type"))
                            )
                            if event_type == "initial-request":
                                # Request setup, not a move: open the game off it.
                                done = await self._referee(None, stream)
                            else:
                                done = await self._referee(frame, stream)
                            if done:
                                break

                to_send = conn.data_to_send()
                if to_send:
                    writer.write(to_send)
                    await writer.drain()
        except (asyncio.CancelledError, ConnectionError):
            pass
        finally:
            writer.close()

    def _respond_headers(
        self, conn: h2.connection.H2Connection, stream: ServerStream
    ) -> None:
        conn.send_headers(
            stream._stream_id,
            [
                (":status", "200"),
                ("content-type", EVENT_STREAM_CONTENT_TYPE),
                ("smithy-protocol", self._smithy_protocol),
            ],
        )


class _FrameDecoder:
    """Decodes whole event-stream frames out of a growing byte buffer.

    ``Event.decode`` needs a complete frame; feeding it a half-arrived frame raises.
    This buffers bytes across reads and yields only frames whose prelude-declared
    length has fully landed, leaving any trailing partial frame for the next read.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[Event]:
        self._buffer.extend(data)
        frames: list[Event] = []
        while (frame := self._take_frame()) is not None:
            frames.append(frame)
        return frames

    def _take_frame(self) -> Event | None:
        if len(self._buffer) < 12:
            return None
        total_length = int.from_bytes(self._buffer[:4], "big")
        if len(self._buffer) < total_length:
            return None
        frame = Event.decode(BytesIO(bytes(self._buffer[:total_length])))
        del self._buffer[:total_length]
        return frame
