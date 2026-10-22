#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""A localhost HTTP/2 server harness for driving generated clients over a real
bidirectional transport. Test-runtime concerns (which client, which shapes, what
to assert) live in the test modules that use this harness."""

import asyncio
import ssl
from io import BytesIO

import h2.config
import h2.connection
import h2.events
import trustme
from smithy_aws_event_stream.events import Event, EventMessage

EVENT_STREAM_CONTENT_TYPE = "application/vnd.amazon.eventstream"


def encode_event(event_type: str, payload: bytes) -> bytes:
    return EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": event_type,
            ":content-type": "application/cbor",
        },
        payload=payload,
    ).encode()


class H2BidiServer:
    """A localhost HTTP/2 server that echoes an event stream over one stream.

    On the request stream it reads the client's initial-request frame, records its
    ``:event-type``, then writes ``response_frames`` back on the response stream,
    exercising a real concurrent bidirectional exchange. ``response_frames`` is the
    already-encoded event-stream body the test wants the server to reply with.
    """

    def __init__(self, response_frames: bytes) -> None:
        self._response_frames = response_frames
        self._ca = trustme.CA()
        self._server_cert = self._ca.issue_cert("localhost", "127.0.0.1")
        self._ca_cert_ctx = self._ca.cert_pem.tempfile()
        self.ca_cert_path = self._ca_cert_ctx.__enter__()
        self.host = "127.0.0.1"
        self.port = 0
        self._server: asyncio.base_events.Server | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self.received_event_types: list[str] = []

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

        request_buffer = bytearray()
        stream_id: int | None = None
        responded = False

        try:
            while not writer.is_closing():
                data = await reader.read(65536)
                if not data:
                    break
                for event in conn.receive_data(data):
                    if isinstance(event, h2.events.RequestReceived):
                        stream_id = event.stream_id
                    elif isinstance(event, h2.events.DataReceived):
                        request_buffer.extend(event.data)
                        conn.acknowledge_received_data(len(event.data), event.stream_id)

                if stream_id is not None and not responded:
                    initial = Event.decode(BytesIO(bytes(request_buffer)))
                    if initial is not None:
                        self.received_event_types.append(
                            str(initial.message.headers[":event-type"])
                        )
                        self._respond(conn, stream_id)
                        responded = True

                to_send = conn.data_to_send()
                if to_send:
                    writer.write(to_send)
                    await writer.drain()
        except (asyncio.CancelledError, ConnectionError):
            pass
        finally:
            writer.close()

    def _respond(self, conn: h2.connection.H2Connection, stream_id: int) -> None:
        conn.send_headers(
            stream_id,
            [
                (":status", "200"),
                ("content-type", EVENT_STREAM_CONTENT_TYPE),
            ],
        )
        conn.send_data(stream_id, self._response_frames, end_stream=True)
