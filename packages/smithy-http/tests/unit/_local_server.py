# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""A local HTTP/1.1 server for testing HTTP clients against real connections."""

import threading
from dataclasses import dataclass, field
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import TracebackType
from typing import Any, Self


@dataclass
class Reply:
    """A response for :py:class:`LocalHTTPServer` to send."""

    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict[str, str])

    chunked: bool = False
    """Send the body with ``Transfer-Encoding: chunked`` rather than a length."""

    chunk_size: int = 64 * 1024
    """The size of each chunk of a chunked body."""

    truncate: bool = False
    """Advertise one more byte than the body has, then close the connection."""

    stall_after: int | None = None
    """Send this many bytes of the body, then stop sending until the server stops."""

    gate: threading.Event | None = None
    """Send the headers, then wait for this event before sending the body."""


class _QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        # Clients closing connections before reading the whole body is expected.
        pass


class LocalHTTPServer:
    """A local HTTP/1.1 server that sends queued replies.

    It records the client port of each request, so tests can tell whether a
    connection was reused. Requests beyond the queued replies get an empty 200.
    """

    def __init__(self) -> None:
        self.replies: list[Reply] = []
        """Replies to send, in order."""

        self.ports: list[int] = []
        """The client port of each request received."""

        self.paths: list[str] = []
        """The request target of each request received."""

        self.bodies: list[tuple[int, str]] = []
        """The length and SHA-256 of each request body received with a length.

        Bodies are hashed as they're read, so a large one isn't held in memory.
        """

        self._stopping = threading.Event()
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, format: str, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                self._handle()

            def do_PUT(self) -> None:
                self._handle()

            def do_POST(self) -> None:
                self._handle()

            def _handle(self) -> None:
                server.paths.append(self.path)
                if length := int(self.headers.get("Content-Length", 0)):
                    digest, received = sha256(), 0
                    while received < length:
                        if not (
                            chunk := self.rfile.read(min(64 * 1024, length - received))
                        ):
                            break
                        digest.update(chunk)
                        received += len(chunk)
                    server.bodies.append((received, digest.hexdigest()))
                try:
                    server._reply(self)
                except (BrokenPipeError, ConnectionResetError):
                    # The client closed the connection before reading everything.
                    self.close_connection = True

        self._httpd = _QuietServer(("127.0.0.1", 0), Handler)
        self.port: int = self._httpd.server_address[1]
        """The port the server listens on, on ``127.0.0.1``."""

        self._thread = threading.Thread(
            target=self._httpd.serve_forever, args=(0.01,), daemon=True
        )
        self._thread.start()

    def _reply(self, handler: BaseHTTPRequestHandler) -> None:
        self.ports.append(handler.client_address[1])
        reply = self.replies.pop(0) if self.replies else Reply()
        handler.send_response(reply.status)
        if reply.chunked:
            handler.send_header("Transfer-Encoding", "chunked")
        else:
            length = len(reply.body) + (1 if reply.truncate else 0)
            handler.send_header("Content-Length", str(length))
        for name, value in reply.headers.items():
            handler.send_header(name, value)
        handler.end_headers()
        handler.wfile.flush()

        if reply.gate is not None:
            reply.gate.wait(timeout=10)
        body = reply.body
        if reply.stall_after is not None:
            handler.wfile.write(body[: reply.stall_after])
            handler.wfile.flush()
            self._stopping.wait(timeout=10)
            handler.close_connection = True
            return
        if reply.chunked:
            for i in range(0, len(body), reply.chunk_size):
                chunk = body[i : i + reply.chunk_size]
                handler.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
            handler.wfile.write(b"0\r\n\r\n")
        else:
            handler.wfile.write(body)
        if reply.truncate:
            handler.close_connection = True

    def close(self) -> None:
        """Stop the server, releasing any stalled replies."""
        self._stopping.set()
        self._httpd.shutdown()
        self._httpd.server_close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
