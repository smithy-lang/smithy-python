#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportMissingTypeStubs=false,reportUnknownMemberType=false
#  flake8: noqa: F811
import asyncio
from asyncio import Future as AsyncFuture
from collections import deque
from collections.abc import AsyncGenerator, AsyncIterable
from concurrent.futures import Future as ConcurrentFuture
from copy import deepcopy
from functools import partial
from io import BufferedIOBase, BytesIO
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Both of these are types that essentially are "castable to bytes/memoryview"
    # Unfortunately they're not exposed anywhere so we have to import them from
    # _typeshed.
    from _typeshed import ReadableBuffer, WriteableBuffer

    # pyright doesn't like optional imports. This is reasonable because if we use these
    # in type hints then they'd result in runtime errors.
    # TODO: add integ tests that import these without the dependendency installed
    from awscrt import http as crt_http
    from awscrt import io as crt_io

try:
    from awscrt import http as crt_http
    from awscrt import io as crt_io

    HAS_CRT = True
except ImportError:
    HAS_CRT = False  # type: ignore

from smithy_core import interfaces as core_interfaces
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import close
from smithy_core.exceptions import MissingDependencyException

from .. import Field, Fields
from .. import interfaces as http_interfaces
from ..exceptions import SmithyHTTPException
from ..interfaces import FieldPosition
from . import interfaces as http_aio_interfaces


def _assert_crt() -> None:
    if not HAS_CRT:
        raise MissingDependencyException(
            "Attempted to use awscrt component, but awscrt is not installed."
        )


class _AWSCRTEventLoop:
    def __init__(self) -> None:
        _assert_crt()
        self.bootstrap = self._initialize_default_loop()

    def _initialize_default_loop(self) -> "crt_io.ClientBootstrap":
        event_loop_group = crt_io.EventLoopGroup(1)
        host_resolver = crt_io.DefaultHostResolver(event_loop_group)
        return crt_io.ClientBootstrap(event_loop_group, host_resolver)


class AWSCRTHTTPResponse(http_aio_interfaces.HTTPResponse):
    def __init__(self, *, status: int, fields: Fields, body: "CRTResponseBody") -> None:
        _assert_crt()
        self._status = status
        self._fields = fields
        self._body = body

    @property
    def status(self) -> int:
        return self._status

    @property
    def fields(self) -> Fields:
        return self._fields

    @property
    def body(self) -> AsyncIterable[bytes]:
        return self.chunks()

    @property
    def reason(self) -> str | None:
        """Optional string provided by the server explaining the status."""
        # TODO: See how CRT exposes reason.
        return None

    async def chunks(self) -> AsyncGenerator[bytes, None]:
        while True:
            chunk = await self._body.next()
            if chunk:
                yield chunk
            else:
                break

    def __repr__(self) -> str:
        return (
            f"AWSCRTHTTPResponse("
            f"status={self.status}, "
            f"fields={self.fields!r}, body=...)"
        )


class CRTResponseBody:
    def __init__(self) -> None:
        self._stream: crt_http.HttpClientStream | None = None
        self._completion_future: AsyncFuture[int] | None = None
        self._chunk_futures: deque[ConcurrentFuture[bytes]] = deque()

        # deque is thread safe and the crt is only going to be writing
        # with one thread anyway, so we *shouldn't* need to gate this
        # behind a lock. In an ideal world, the CRT would expose
        # an interface that better matches python's async.
        self._received_chunks: deque[bytes] = deque()

    def set_stream(self, stream: "crt_http.HttpClientStream") -> None:
        if self._stream is not None:
            raise SmithyHTTPException("Stream already set on AWSCRTHTTPResponse object")
        self._stream = stream
        concurrent_future: ConcurrentFuture[int] = stream.completion_future
        self._completion_future = asyncio.wrap_future(concurrent_future)
        self._completion_future.add_done_callback(self._on_complete)
        self._stream.activate()

    def on_body(self, chunk: bytes, **kwargs: Any) -> None:  # pragma: crt-callback
        # TODO: update back pressure window once CRT supports it
        if self._chunk_futures:
            future = self._chunk_futures.popleft()
            future.set_result(chunk)
        else:
            self._received_chunks.append(chunk)

    async def next(self) -> bytes:
        if self._completion_future is None:
            raise SmithyHTTPException("Stream not set")

        # TODO: update backpressure window once CRT supports it
        if self._received_chunks:
            return self._received_chunks.popleft()
        elif self._completion_future.done():
            return b""
        else:
            future = ConcurrentFuture[bytes]()
            self._chunk_futures.append(future)
            return await asyncio.wrap_future(future)

    def _on_complete(
        self, completion_future: AsyncFuture[int]
    ) -> None:  # pragma: crt-callback
        for future in self._chunk_futures:
            future.set_result(b"")
        self._chunk_futures.clear()


class CRTResponseFactory:
    def __init__(self, body: CRTResponseBody) -> None:
        self._body = body
        self._response_future = ConcurrentFuture[AWSCRTHTTPResponse]()

    def on_response(
        self, status_code: int, headers: list[tuple[str, str]], **kwargs: Any
    ) -> None:  # pragma: crt-callback
        fields = Fields()
        for header_name, header_val in headers:
            try:
                fields[header_name].add(header_val)
            except KeyError:
                fields[header_name] = Field(
                    name=header_name,
                    values=[header_val],
                    kind=FieldPosition.HEADER,
                )

        self._response_future.set_result(
            AWSCRTHTTPResponse(
                status=status_code,
                fields=fields,
                body=self._body,
            )
        )

    async def await_response(self) -> AWSCRTHTTPResponse:
        return await asyncio.wrap_future(self._response_future)

    def set_done_callback(self, stream: "crt_http.HttpClientStream") -> None:
        stream.completion_future.add_done_callback(self._cancel)

    def _cancel(self, completion_future: ConcurrentFuture[int | Exception]) -> None:
        if not self._response_future.done():
            self._response_future.cancel()


ConnectionPoolKey = tuple[str, str, int | None]
ConnectionPoolDict = dict[ConnectionPoolKey, "crt_http.HttpClientConnection"]


class AWSCRTHTTPClientConfig(http_interfaces.HTTPClientConfiguration):
    def __post_init__(self) -> None:
        _assert_crt()


class AWSCRTHTTPClient(http_aio_interfaces.HTTPClient):
    _HTTP_PORT = 80
    _HTTPS_PORT = 443

    def __init__(
        self,
        eventloop: _AWSCRTEventLoop | None = None,
        client_config: AWSCRTHTTPClientConfig | None = None,
    ) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        _assert_crt()
        self._config = client_config or AWSCRTHTTPClientConfig()
        if eventloop is None:
            eventloop = _AWSCRTEventLoop()
        self._eventloop = eventloop
        self._client_bootstrap = self._eventloop.bootstrap
        self._tls_ctx = crt_io.ClientTlsContext(crt_io.TlsContextOptions())
        self._socket_options = crt_io.SocketOptions()
        self._connections: ConnectionPoolDict = {}
        self._async_reads: set[asyncio.Task[Any]] = set()

    async def send(
        self,
        request: http_aio_interfaces.HTTPRequest,
        *,
        request_config: http_aio_interfaces.HTTPRequestConfiguration | None = None,
    ) -> AWSCRTHTTPResponse:
        """Send HTTP request using awscrt client.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        crt_request, crt_body = await self._marshal_request(request)
        connection = await self._get_connection(request.destination)
        response_body = CRTResponseBody()
        response_factory = CRTResponseFactory(response_body)
        crt_stream = connection.request(
            crt_request,
            response_factory.on_response,
            response_body.on_body,
        )
        response_factory.set_done_callback(crt_stream)
        response_body.set_stream(crt_stream)
        crt_stream.completion_future.add_done_callback(
            partial(self._close_input_body, body=crt_body)
        )

        response = await response_factory.await_response()
        if response.status != 200 and response.status >= 300:
            await close(crt_body)

        return response

    def _close_input_body(
        self, future: ConcurrentFuture[int], *, body: "BufferableByteStream | BytesIO"
    ) -> None:
        if future.exception(timeout=0):
            body.close()

    async def _create_connection(
        self, url: core_interfaces.URI
    ) -> "crt_http.HttpClientConnection":
        """Builds and validates connection to ``url``"""
        connect_future = self._build_new_connection(url)
        connection = await asyncio.wrap_future(connect_future)
        self._validate_connection(connection)
        return connection

    async def _get_connection(
        self, url: core_interfaces.URI
    ) -> "crt_http.HttpClientConnection":
        # TODO: Use CRT connection pooling instead of this basic kind
        connection_key = (url.scheme, url.host, url.port)
        connection = self._connections.get(connection_key)

        if connection and connection.is_open():
            return connection

        connection = await self._create_connection(url)
        self._connections[connection_key] = connection
        return connection

    def _build_new_connection(
        self, url: core_interfaces.URI
    ) -> ConcurrentFuture["crt_http.HttpClientConnection"]:
        if url.scheme == "http":
            port = self._HTTP_PORT
            tls_connection_options = None
        elif url.scheme == "https":
            port = self._HTTPS_PORT
            tls_connection_options = self._tls_ctx.new_connection_options()
            tls_connection_options.set_server_name(url.host)
            # TODO: Support TLS configuration, including alpn
            tls_connection_options.set_alpn_list(["h2", "http/1.1"])
        else:
            raise SmithyHTTPException(
                f"AWSCRTHTTPClient does not support URL scheme {url.scheme}"
            )
        if url.port is not None:
            port = url.port

        connect_future: ConcurrentFuture[crt_http.HttpClientConnection] = (
            crt_http.HttpClientConnection.new(
                bootstrap=self._client_bootstrap,
                host_name=url.host,
                port=port,
                socket_options=self._socket_options,
                tls_connection_options=tls_connection_options,
            )
        )
        return connect_future

    def _validate_connection(self, connection: "crt_http.HttpClientConnection") -> None:
        """Validates an existing connection against the client config.

        Checks performed:
        * If ``force_http_2`` is enabled: Is the connection HTTP/2?
        """
        force_http_2 = self._config.force_http_2
        if force_http_2 and connection.version is not crt_http.HttpVersion.Http2:
            connection.close()
            negotiated = crt_http.HttpVersion(connection.version).name
            raise SmithyHTTPException(f"HTTP/2 could not be negotiated: {negotiated}")

    def _render_path(self, url: core_interfaces.URI) -> str:
        path = url.path if url.path is not None else "/"
        query = f"?{url.query}" if url.query is not None else ""
        return f"{path}{query}"

    async def _marshal_request(
        self, request: http_aio_interfaces.HTTPRequest
    ) -> tuple["crt_http.HttpRequest", "BufferableByteStream | BytesIO"]:
        """Create :py:class:`awscrt.http.HttpRequest` from
        :py:class:`smithy_http.aio.HTTPRequest`"""
        headers_list = []
        if "host" not in request.fields:
            request.fields.set_field(
                Field(name="host", values=[request.destination.host])
            )

        if "accept" not in request.fields:
            request.fields.set_field(Field(name="accept", values=["*/*"]))

        for fld in request.fields.entries.values():
            # TODO: Use literal values for "header"/"trailer".
            if fld.kind.value != FieldPosition.HEADER.value:
                continue
            for val in fld.values:
                headers_list.append((fld.name, val))

        path = self._render_path(request.destination)
        headers = crt_http.HttpHeaders(headers_list)

        body = request.body
        if isinstance(body, bytes | bytearray):
            # If the body is already directly in memory, wrap in a BytesIO to hand
            # off to CRT.
            crt_body = BytesIO(body)
        else:
            # If the body is async, or potentially very large, start up a task to read
            # it into the intermediate object that CRT needs. By using
            # asyncio.create_task we'll start the coroutine without having to
            # explicitly await it.
            crt_body = BufferableByteStream()

            if not isinstance(body, AsyncIterable):
                body = AsyncBytesReader(body)

            # Start the read task in the background.
            read_task = asyncio.create_task(self._consume_body_async(body, crt_body))

            # Keep track of the read task so that it doesn't get garbage colllected,
            # and stop tracking it once it's done.
            self._async_reads.add(read_task)
            read_task.add_done_callback(self._async_reads.discard)

        crt_request = crt_http.HttpRequest(
            method=request.method,
            path=path,
            headers=headers,
            body_stream=crt_body,
        )
        return crt_request, crt_body

    async def _consume_body_async(
        self, source: AsyncIterable[bytes], dest: "BufferableByteStream"
    ) -> None:
        try:
            async for chunk in source:
                dest.write(chunk)
        except Exception:
            dest.close()
            raise
        finally:
            await close(source)
        dest.end_stream()

    def __deepcopy__(self, memo: Any) -> "AWSCRTHTTPClient":
        return AWSCRTHTTPClient(
            eventloop=self._eventloop,
            client_config=deepcopy(self._config),
        )


# This is adapted from the transcribe streaming sdk
class BufferableByteStream(BufferedIOBase):
    """A non-blocking bytes buffer."""

    def __init__(self) -> None:
        # We're always manipulating the front and back of the buffer, so a deque
        # will be much more efficient than a list.
        self._chunks: deque[bytes] = deque()
        self._closed = False
        self._done = False

    def read(self, size: int | None = -1) -> bytes:
        if self._closed:
            return b""

        if len(self._chunks) == 0:
            if self._done:
                self.close()
                return b""
            else:
                # When the CRT recieves this, it'll try again
                raise BlockingIOError("read")

        # We could compile all the chunks here instead of just returning
        # the one, BUT the CRT will keep calling read until empty bytes
        # are returned. So it's actually better to just return one chunk
        # since combining them would have some potentially bad memory
        # usage issues.
        result = self._chunks.popleft()
        if size is not None and size > 0:
            remainder = result[size:]
            result = result[:size]
            if remainder:
                self._chunks.appendleft(remainder)

        if self._done and len(self._chunks) == 0:
            self.close()

        return result

    def read1(self, size: int = -1) -> bytes:
        return self.read(size)

    def readinto(self, buffer: "WriteableBuffer") -> int:
        if not isinstance(buffer, memoryview):
            buffer = memoryview(buffer).cast("B")

        data = self.read(len(buffer))  # type: ignore
        n = len(data)
        buffer[:n] = data
        return n

    def write(self, buffer: "ReadableBuffer") -> int:
        if not isinstance(buffer, bytes):
            raise ValueError(
                f"Unexpected value written to BufferableByteStream. "
                f"Only bytes are support but {type(buffer)} was provided."
            )

        if self._closed:
            raise OSError("Stream is completed and doesn't support further writes.")

        if buffer:
            self._chunks.append(buffer)
        return len(buffer)

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True
        self._done = True

        # Clear out the remaining chunks so that they don't sit around in memory.
        self._chunks.clear()

    def end_stream(self) -> None:
        """End the stream, letting any remaining chunks be read before it is closed."""
        if len(self._chunks) == 0:
            self.close()
        else:
            self._done = True
