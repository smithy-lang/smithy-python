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
from collections.abc import AsyncIterable
from concurrent.futures import Future
from io import BytesIO
from itertools import chain
from threading import Lock
from typing import Any, AsyncGenerator, Awaitable, cast

from awscrt import http as crt_http
from awscrt import io as crt_io

from ... import interfaces
from ...exceptions import SmithyException
from . import FieldPosition, Fields, HTTPResponse


class HTTPException(SmithyException):
    """TODO: Improve exception handling

    Error handling in smithy-python needs to be designed out.
    """


class _AWSCRTEventLoop:
    def __init__(self) -> None:
        self.bootstrap = self._initialize_default_loop()

    def _initialize_default_loop(self) -> crt_io.ClientBootstrap:
        event_loop_group = crt_io.EventLoopGroup(1)
        host_resolver = crt_io.DefaultHostResolver(event_loop_group)
        return crt_io.ClientBootstrap(event_loop_group, host_resolver)


class AwsCrtHttpResponse(interfaces.http.HTTPResponse):
    def __init__(self) -> None:
        self._stream: crt_http.HttpClientStream | None = None
        self._status_code_future: Future[int] = Future()
        self._headers_future: Future[interfaces.http.Fields] = Future()
        self._chunk_futures: list[Future[bytes]] = []
        self._received_chunks: list[bytes] = []
        self._chunk_lock: Lock = Lock()

    def _set_stream(self, stream: crt_http.HttpClientStream) -> None:
        if self._stream is not None:
            raise HTTPException("Stream already set on _AwsCrtHttpResponse object")
        self._stream = stream
        self._stream.completion_future.add_done_callback(self._on_complete)
        self._stream.activate()

    def _on_headers(
        self, status_code: int, headers: interfaces.http.Fields, **kwargs: Any
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

    def _get_chunk_future(self) -> Future[bytes]:
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
        self, completion_future: Future[int]
    ) -> None:  # pragma: crt-callback
        with self._chunk_lock:
            if self._chunk_futures:
                future = self._chunk_futures.pop(0)
                future.set_result(b"")

    @property
    def body(self) -> AsyncIterable[bytes]:
        return self.chunks()

    @property
    def status(self) -> int:
        return self._status_code_future.result()

    @property
    def headers(self) -> Awaitable[Fields]:
        if self._stream is None:
            raise HTTPException("Stream not set")
        return asyncio.wrap_future(self._headers_future)

    @property
    def done(self) -> bool:
        if self._stream is None:
            raise HTTPException("Stream not set")
        # awscrt does not type-annotate self._stream.completion_future
        fut = cast(Future[int], self._stream.completion_future)
        return fut.done()

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

    async def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        body = b""
        async for chunk in self.body:
            body += chunk
        return body


ConnectionPoolKey = tuple[str, str, int | None]
ConnectionPoolDict = dict[ConnectionPoolKey, crt_http.HttpClientConnection]


class AwsCrtHttpClientConfig(interfaces.http.HttpClientConfiguration):
    pass


class AwsCrtHttpClient(interfaces.http.HttpClient):
    _HTTP_PORT = 80
    _HTTPS_PORT = 443

    def __init__(
        self,
        eventloop: _AWSCRTEventLoop | None = None,
        client_config: AwsCrtHttpClientConfig | None = None,
    ) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        self._config = (
            AwsCrtHttpClientConfig() if client_config is None else client_config
        )
        if eventloop is None:
            eventloop = _AWSCRTEventLoop()
        self._eventloop = eventloop
        self._client_bootstrap = self._eventloop.bootstrap
        self._tls_ctx = crt_io.ClientTlsContext(crt_io.TlsContextOptions())
        self._socket_options = crt_io.SocketOptions()
        self._connections: ConnectionPoolDict = {}

    async def send(
        self,
        request: interfaces.http.HTTPRequest,
        request_config: interfaces.http.HttpRequestConfiguration | None = None,
    ) -> HTTPResponse:
        """
        Send HTTP request using awscrt client.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        crt_request = await self._marshal_request(request)
        connection = await self._get_connection(request.destination)
        crt_response = AwsCrtHttpResponse()
        crt_stream = connection.request(
            crt_request,
            crt_response._on_headers,
            crt_response._on_body,
        )
        crt_response._set_stream(crt_stream)
        return crt_response

    async def _create_connection(
        self, url: interfaces.URI
    ) -> crt_http.HttpClientConnection:
        """Builds and validates connection to ``url``, returns it as ``asyncio.Future``"""
        connect_future = self._build_new_connection(url)
        connection = await asyncio.wrap_future(connect_future)
        self._validate_connection(connection)
        return connection

    async def _get_connection(
        self, url: interfaces.URI
    ) -> crt_http.HttpClientConnection:
        # TODO: Use CRT connection pooling instead of this basic kind
        connection_key = (url.scheme, url.host, url.port)
        if connection_key in self._connections:
            return self._connections[connection_key]
        else:
            connection = await self._create_connection(url)
            self._connections[connection_key] = connection
            return connection

    def _build_new_connection(
        self, url: interfaces.URI
    ) -> Future[crt_http.HttpClientConnection]:
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
            raise HTTPException(
                f"AwsCrtHttpClient does not support URL scheme {url.scheme}"
            )
        if url.port is not None:
            port = url.port

        connect_future: Future[
            crt_http.HttpClientConnection
        ] = crt_http.HttpClientConnection.new(
            bootstrap=self._client_bootstrap,
            host_name=url.host,
            port=port,
            socket_options=self._socket_options,
            tls_connection_options=tls_connection_options,
        )
        return connect_future

    def _validate_connection(self, connection: crt_http.HttpClientConnection) -> None:
        """Validates an existing connection against the client config.

        Checks performed:
        * If ``force_http_2`` is enabled: Is the connection HTTP/2?
        """
        force_http_2 = self._config.force_http_2
        if force_http_2 and connection.version is not crt_http.HttpVersion.Http2:
            connection.close()
            negotiated = crt_http.HttpVersion(connection.version).name
            raise HTTPException(f"HTTP/2 could not be negotiated: {negotiated}")

    def _render_path(self, url: interfaces.URI) -> str:
        path = url.path if url.path is not None else "/"
        query = f"?{url.query}" if url.query is not None else ""
        return f"{path}{query}"

    async def _marshal_request(
        self, request: interfaces.http.HTTPRequest
    ) -> crt_http.HttpRequest:
        """
        Create :py:class:`awscrt.http.HttpRequest` from
        :py:class:`smithy_python.interfaces.http.HTTPRequest`
        """
        headers_list = []
        for fld in request.fields.entries.values():
            if fld.kind != FieldPosition.HEADER:
                continue
            for val in fld.values:
                headers_list.append((fld.name, val))

        path = self._render_path(request.destination)
        headers = crt_http.HttpHeaders(headers_list)
        body = BytesIO(await request.consume_body())

        crt_request = crt_http.HttpRequest(
            method=request.method,
            path=path,
            headers=headers,
            body_stream=body,
        )
        return crt_request
