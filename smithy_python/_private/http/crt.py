# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


import asyncio

from io import BytesIO
from threading import Lock
from awscrt import io, http  # type: ignore
from concurrent.futures import Future
from typing import Optional, List, Tuple, Awaitable, AsyncGenerator, Any, Dict
from smithy_python._private.http import URL, Request, Response


HeadersList = List[Tuple[str, str]]


class HTTPException(Exception):
    """TODO: Improve exception handling """


class AWSCRTEventLoop:
    def __init__(self) -> None:
        self.bootstrap = self._initialize_default_loop()

    def _initialize_default_loop(self) -> io.ClientBootstrap:
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        return io.ClientBootstrap(event_loop_group, host_resolver)


class _AwsCrtHttpResponse:
    def __init__(self) -> None:
        self._stream: Optional[http.HttpClientStream] = None
        self._status_code_future: Future[int] = Future()
        self._headers_future: Future[HeadersList] = Future()
        self._chunk_futures: List[Future[bytes]] = []
        self._received_chunks: List[bytes] = []
        self._chunk_lock: Lock = Lock()

    async def consume_body(self) -> bytes:
        body = b""
        async for chunk in self.chunks():
            body += chunk
        return body

    def _set_stream(self, stream: http.HttpClientStream) -> None:
        if self._stream is not None:
            raise HTTPException("Stream already set on _AwsCrtHttpResponse object")
        self._stream = stream
        self._stream.completion_future.add_done_callback(self._on_complete)
        self._stream.activate()

    @property
    def status_code(self) -> Awaitable[int]:
        return asyncio.wrap_future(self._status_code_future)

    @property
    def headers(self) -> Awaitable[HeadersList]:
        if self._stream is None:
            raise HTTPException("Stream not set")
        return asyncio.wrap_future(self._headers_future)

    @property
    def done(self) -> Awaitable[bool]:
        if self._stream is None:
            raise HTTPException("Stream not set")
        return asyncio.wrap_future(self._stream.completion_future)

    def get_chunk(self) -> Awaitable[bytes]:
        if self._stream is None:
            raise HTTPException("Stream not set")
        with self._chunk_lock:
            future: Future[bytes] = Future()
            # TODO: update backpressure window once CRT supports it
            if self._received_chunks:
                chunk = self._received_chunks.pop(0)
                future.set_result(chunk)
            elif self._stream.completion_future.done():
                future.set_result(b"")
            else:
                self._chunk_futures.append(future)
            return asyncio.wrap_future(future)

    async def chunks(self) -> AsyncGenerator[bytes, None]:
        while True:
            chunk = await self.get_chunk()
            if chunk:
                yield chunk
            else:
                break

    def _on_headers(
        self, status_code: int, headers: HeadersList, **kwargs: Any
    ) -> None:
        self._status_code_future.set_result(status_code)
        self._headers_future.set_result(headers)

    def _on_body(self, chunk: bytes, **kwargs: Any) -> None:
        with self._chunk_lock:
            # TODO: update back pressure window once CRT supports it
            if self._chunk_futures:
                future = self._chunk_futures.pop(0)
                future.set_result(chunk)
            else:
                self._received_chunks.append(chunk)

    # Type resolution is a bit strange here and this will fail at runtime if
    # Future[int] is directly used. Not sure why it's an issue here and not
    # other places.
    def _on_complete(self, completion_future: "Future[int]") -> None:
        with self._chunk_lock:
            if self._chunk_futures:
                future = self._chunk_futures.pop(0)
                future.set_result(b"")


ConnectionPoolKey = Tuple[str, str, Optional[int]]
ConnectionPoolDict = Dict[ConnectionPoolKey, http.HttpClientConnection]


class AwsCrtHttpSession:
    _HTTP_PORT = 80
    _HTTPS_PORT = 443

    def __init__(self, eventloop: Optional[AWSCRTEventLoop] = None) -> None:
        if eventloop is None:
            eventloop = AWSCRTEventLoop()
        self._eventloop = eventloop
        self._client_bootstrap = self._eventloop.bootstrap
        self._tls_ctx = io.ClientTlsContext(io.TlsContextOptions())
        self._socket_options = io.SocketOptions()
        self._connections: ConnectionPoolDict = {}

    async def _create_connection(self, url: URL) -> http.HttpClientConnection:
        if url.scheme == "http":
            port = self._HTTP_PORT
            tls_connection_options = None
        else:
            port = self._HTTPS_PORT
            tls_connection_options = self._tls_ctx.new_connection_options()
            tls_connection_options.set_server_name(url.hostname)
            tls_connection_options.set_alpn_list(["h2"])
        if url.port is not None:
            port = url.port

        connect_future = http.HttpClientConnection.new(
            bootstrap=self._client_bootstrap,
            host_name=url.hostname,
            port=port,
            socket_options=self._socket_options,
            tls_connection_options=tls_connection_options,
        )
        connection = await asyncio.wrap_future(connect_future)

        if connection.version is not http.HttpVersion.Http2:
            connection.close()
            raise HTTPException("HTTP/2 could not be negotiated: {connection.version}")

        return connection

    async def _get_connection(self, url: URL) -> http.HttpClientConnection:
        # TODO: Use CRT connection pooling instead of this basic kind
        if not url.hostname:
            raise HTTPException(f"Invalid host name: {url.hostname}")

        connection_key = (url.scheme, url.hostname, url.port)
        if connection_key in self._connections:
            return self._connections[connection_key]
        else:
            connection = await self._create_connection(url)
            self._connections[connection_key] = connection
            return connection

    def _render_path(self, url: URL) -> str:
        path = url.path
        if not path:
            # TODO: Conflating None and empty "" path?
            path = "/"
        if url.query_params:
            # TODO: Do we handle URL escaping here?
            query = "&".join(f"{k}={v}" for k, v in url.query_params)
            path = path + "?" + query
        return path

    async def send(self, request: Request) -> Response:
        headers = None
        if isinstance(request.headers, list):
            headers = http.HttpHeaders(request.headers)

        body: Optional[BytesIO]
        if request.body is not None:
            body = BytesIO(request.body)
        else:
            body = None

        crt_request = http.HttpRequest(
            method=request.method,
            path=self._render_path(request.url),
            headers=headers,
            body_stream=body,
        )

        connection = await self._get_connection(request.url)
        crt_response = _AwsCrtHttpResponse()
        crt_stream = connection.request(
            crt_request, crt_response._on_headers, crt_response._on_body,
        )
        crt_response._set_stream(crt_stream)

        # TODO: Trouble in async city, do we force header/status resolution here?
        # A sync interface can "hide" the blocking behind a property, async can't
        # TODO: Figuring out streaming bodies
        return Response(
            status_code=await crt_response.status_code,
            headers=await crt_response.headers,
            body=await crt_response.consume_body(),
        )
