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
from concurrent.futures import Future
from io import BytesIO
from threading import Lock
from typing import Any, AsyncGenerator, Awaitable, Generator

from awscrt import http, io

from smithy_python._private.http import Response
from smithy_python.interfaces import http as http_interface

HeadersList = list[tuple[str, str]]


class HTTPException(Exception):
    """TODO: Improve exception handling

    This should probably extend from a base smithy error or something similar.
    In general, error handling in smithy-python needs to be designed out.
    """


class AWSCRTEventLoop:
    def __init__(self) -> None:
        self.bootstrap = self._initialize_default_loop()

    def _initialize_default_loop(self) -> io.ClientBootstrap:
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        return io.ClientBootstrap(event_loop_group, host_resolver)


class _BaseAwsCrtHttpResponse:
    def __init__(self) -> None:
        self._stream: http.HttpClientStream | None = None
        self._status_code_future: Future[int] = Future()
        self._headers_future: Future[HeadersList] = Future()
        self._chunk_futures: list[Future[bytes]] = []
        self._received_chunks: list[bytes] = []
        self._chunk_lock: Lock = Lock()

    def _set_stream(self, stream: http.HttpClientStream) -> None:
        if self._stream is not None:
            raise HTTPException("Stream already set on _AwsCrtHttpResponse object")
        self._stream = stream
        self._stream.completion_future.add_done_callback(self._on_complete)
        self._stream.activate()

    def _on_headers(
        self, status_code: int, headers: HeadersList, **kwargs: Any
    ) -> None:  # pragma: crt-callback
        self._status_code_future.set_result(status_code)
        self._headers_future.set_result(headers)

    def _on_body(self, chunk: bytes, **kwargs: Any) -> None:  # pragma: crt-callback
        with self._chunk_lock:
            # TODO: update back pressure window once CRT supports it
            if self._chunk_futures:
                future = self._chunk_futures.pop(0)
                future.set_result(chunk)
            else:
                self._received_chunks.append(chunk)

    def _get_chunk_future(self) -> "Future[bytes]":
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
        return future

    def _on_complete(
        self, completion_future: "Future[int]"
    ) -> None:  # pragma: crt-callback
        with self._chunk_lock:
            if self._chunk_futures:
                future = self._chunk_futures.pop(0)
                future.set_result(b"")


class _AsyncAwsCrtHttpResponse(_BaseAwsCrtHttpResponse):
    async def consume_body(self) -> bytes:
        body = b""
        async for chunk in self.chunks():
            body += chunk
        return body

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
        future = self._get_chunk_future()
        return asyncio.wrap_future(future)

    async def chunks(self) -> AsyncGenerator[bytes, None]:
        while True:
            chunk = await self.get_chunk()
            if chunk:
                yield chunk
            else:
                break


class _SyncAwsCrtHttpResponse(_BaseAwsCrtHttpResponse):
    def consume_body(self) -> bytes:
        body = b""
        for chunk in self.chunks():
            body += chunk
        return body

    @property
    def status_code(self) -> int:
        return self._status_code_future.result()

    @property
    def headers(self) -> HeadersList:
        if self._stream is None:
            raise HTTPException("Stream not set")
        return self._headers_future.result()

    @property
    def done(self) -> bool:
        if self._stream is None:
            raise HTTPException("Stream not set")
        future: Future[bool] = self._stream.completion_future
        return future.result()

    def get_chunk(self) -> bytes:
        future = self._get_chunk_future()
        return future.result()

    def chunks(self) -> Generator[bytes, None, None]:
        while True:
            chunk = self.get_chunk()
            if chunk:
                yield chunk
            else:
                break


ConnectionPoolKey = tuple[str, str, int | None]
ConnectionPoolDict = dict[ConnectionPoolKey, http.HttpClientConnection]


class AwsCrtHttpSessionConfig:
    def __init__(
        self,
        force_http_2: bool | None = None,
    ) -> None:
        if force_http_2 is None:
            force_http_2 = False
        self.force_http_2: bool = force_http_2


class _BaseAwsCrtHttpSession:
    _HTTP_PORT = 80
    _HTTPS_PORT = 443

    def __init__(
        self,
        eventloop: AWSCRTEventLoop | None = None,
        config: AwsCrtHttpSessionConfig | None = None,
    ) -> None:
        if eventloop is None:
            eventloop = AWSCRTEventLoop()
        self._eventloop = eventloop
        if config is None:
            config = AwsCrtHttpSessionConfig()
        self._config: AwsCrtHttpSessionConfig = config
        self._client_bootstrap = self._eventloop.bootstrap
        self._tls_ctx = io.ClientTlsContext(io.TlsContextOptions())
        self._socket_options = io.SocketOptions()
        self._connections: ConnectionPoolDict = {}

    def _build_new_connection(
        self, url: http_interface.URL
    ) -> "Future[http.HttpClientConnection]":
        if url.scheme == "http":
            port = self._HTTP_PORT
            tls_connection_options = None
        else:
            port = self._HTTPS_PORT
            tls_connection_options = self._tls_ctx.new_connection_options()
            tls_connection_options.set_server_name(url.hostname)
            # TODO: Support TLS configuration, including alpn
            tls_connection_options.set_alpn_list(["h2", "http/1.1"])
        if url.port is not None:
            port = url.port

        connect_future: Future[
            http.HttpClientConnection
        ] = http.HttpClientConnection.new(
            bootstrap=self._client_bootstrap,
            host_name=url.hostname,
            port=port,
            socket_options=self._socket_options,
            tls_connection_options=tls_connection_options,
        )
        return connect_future

    def _validate_connection(self, connection: http.HttpClientConnection) -> None:
        force_http_2 = self._config.force_http_2
        if force_http_2 and connection.version is not http.HttpVersion.Http2:
            connection.close()
            negotiated = http.HttpVersion(connection.version).name
            raise HTTPException(f"HTTP/2 could not be negotiated: {negotiated}")

    def _render_path(self, url: http_interface.URL) -> str:
        path = url.path
        if not path:
            # TODO: Conflating None and empty "" path?
            path = "/"
        if url.query_params:
            # TODO: Do we handle URL escaping here?
            query = "&".join(f"{k}={v}" for k, v in url.query_params)
            path = path + "?" + query
        return path

    def _validate_url(self, url: http_interface.URL) -> None:
        if not url.hostname:
            raise HTTPException(f"Invalid host name: {url.hostname}")

    def _build_new_request(self, request: http_interface.Request) -> http.HttpRequest:
        headers = None
        if isinstance(request.headers, list):
            headers = http.HttpHeaders(request.headers)

        body: Any
        if isinstance(request.body, bytes):
            body = BytesIO(request.body)
        else:
            body = request.body

        crt_request = http.HttpRequest(
            method=request.method,
            path=self._render_path(request.url),
            headers=headers,
            body_stream=body,
        )
        return crt_request


class AsyncAwsCrtHttpSession(_BaseAwsCrtHttpSession):
    async def _create_connection(
        self, url: http_interface.URL
    ) -> http.HttpClientConnection:
        connect_future = self._build_new_connection(url)
        connection = await asyncio.wrap_future(connect_future)
        self._validate_connection(connection)
        return connection

    async def _get_connection(
        self, url: http_interface.URL
    ) -> http.HttpClientConnection:
        # TODO: Use CRT connection pooling instead of this basic kind
        self._validate_url(url)
        connection_key = (url.scheme, url.hostname, url.port)
        if connection_key in self._connections:
            return self._connections[connection_key]
        else:
            connection = await self._create_connection(url)
            self._connections[connection_key] = connection
            return connection

    async def send(self, request: http_interface.Request) -> http_interface.Response:
        crt_request = self._build_new_request(request)
        connection = await self._get_connection(request.url)
        crt_response = _AsyncAwsCrtHttpResponse()
        crt_stream = connection.request(
            crt_request,
            crt_response._on_headers,
            crt_response._on_body,
        )
        crt_response._set_stream(crt_stream)

        return Response(
            status_code=await crt_response.status_code,
            headers=await crt_response.headers,
            body=crt_response,
        )


class SyncAwsCrtHttpSession(_BaseAwsCrtHttpSession):
    def _get_connection(self, url: http_interface.URL) -> http.HttpClientConnection:
        # TODO: Use CRT connection pooling instead of this basic kind
        self._validate_url(url)
        connection_key = (url.scheme, url.hostname, url.port)
        if connection_key in self._connections:
            return self._connections[connection_key]
        else:
            connection = self._build_new_connection(url).result()
            self._validate_connection(connection)
            self._connections[connection_key] = connection
            return connection

    def send(self, request: http_interface.Request) -> http_interface.Response:
        crt_request = self._build_new_request(request)
        connection = self._get_connection(request.url)
        crt_response = _SyncAwsCrtHttpResponse()
        crt_stream = connection.request(
            crt_request,
            crt_response._on_headers,
            crt_response._on_body,
        )
        crt_response._set_stream(crt_stream)

        return Response(
            status_code=crt_response.status_code,
            headers=crt_response.headers,
            body=crt_response,
        )
