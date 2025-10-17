#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportMissingTypeStubs=false,reportUnknownMemberType=false
#  flake8: noqa: F811
from collections.abc import AsyncGenerator, AsyncIterable
from copy import deepcopy
from dataclasses import dataclass
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # pyright doesn't like optional imports. This is reasonable because if we use these
    # in type hints then they'd result in runtime errors.
    # TODO: add integ tests that import these without the dependendency installed
    from awscrt import http as crt_http
    from awscrt import io as crt_io
    from awscrt.aio.http import (
        AIOHttpClientConnectionUnified,
        AIOHttpClientStreamUnified,
    )

try:
    from awscrt import http as crt_http
    from awscrt import io as crt_io
    from awscrt.aio.http import (
        AIOHttpClientConnectionUnified,
        AIOHttpClientStreamUnified,
    )

    HAS_CRT = True
except ImportError:
    HAS_CRT = False  # type: ignore

from smithy_core import interfaces as core_interfaces
from smithy_core.aio import interfaces as core_aio_interfaces
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import MissingDependencyError

from .. import Field, Fields
from .. import interfaces as http_interfaces
from ..exceptions import SmithyHTTPError
from ..interfaces import FieldPosition
from . import interfaces as http_aio_interfaces

# Default buffer size for reading from streams (8 KB)
DEFAULT_READ_BUFFER_SIZE = 8192


def _assert_crt() -> None:
    if not HAS_CRT:
        raise MissingDependencyError(
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
    def __init__(
        self,
        *,
        status: int,
        fields: Fields,
        stream: "AIOHttpClientStreamUnified",
    ) -> None:
        _assert_crt()
        self._status = status
        self._fields = fields
        self._stream = stream

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
            chunk = await self._stream.get_next_response_chunk()
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


ConnectionPoolKey = tuple[str, str, int | None]
ConnectionPoolDict = dict[ConnectionPoolKey, "AIOHttpClientConnectionUnified"]


@dataclass(kw_only=True)
class AWSCRTHTTPClientConfig(http_interfaces.HTTPClientConfiguration):
    """AWS CRT HTTP client configuration.

    :param read_buffer_size: The buffer size in bytes to use when reading from streams.
        Defaults to 8192 (8 KB).
    """

    read_buffer_size: int = DEFAULT_READ_BUFFER_SIZE

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
        crt_request = self._marshal_request(request)
        connection = await self._get_connection(request.destination)

        # Convert body to async iterator for request_body_generator
        body_generator = self._create_body_generator(request.body)

        crt_stream = connection.request(
            crt_request,
            request_body_generator=body_generator,
        )

        return await self._await_response(crt_stream)

    async def _await_response(
        self, stream: "AIOHttpClientStreamUnified"
    ) -> AWSCRTHTTPResponse:
        status_code = await stream.get_response_status_code()
        headers = await stream.get_response_headers()
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
        return AWSCRTHTTPResponse(
            status=status_code,
            fields=fields,
            stream=stream,
        )

    async def _create_connection(
        self, url: core_interfaces.URI
    ) -> "AIOHttpClientConnectionUnified":
        """Builds and validates connection to ``url``"""
        connection = await self._build_new_connection(url)
        await self._validate_connection(connection)
        return connection

    async def _get_connection(
        self, url: core_interfaces.URI
    ) -> "AIOHttpClientConnectionUnified":
        # TODO: Use CRT connection pooling instead of this basic kind
        connection_key = (url.scheme, url.host, url.port)
        connection = self._connections.get(connection_key)

        if connection and connection.is_open():
            return connection

        connection = await self._create_connection(url)
        self._connections[connection_key] = connection
        return connection

    async def _build_new_connection(
        self, url: core_interfaces.URI
    ) -> "AIOHttpClientConnectionUnified":
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
            raise SmithyHTTPError(
                f"AWSCRTHTTPClient does not support URL scheme {url.scheme}"
            )
        if url.port is not None:
            port = url.port

        return await AIOHttpClientConnectionUnified.new(
            bootstrap=self._client_bootstrap,
            host_name=url.host,
            port=port,
            socket_options=self._socket_options,
            tls_connection_options=tls_connection_options,
        )

    async def _validate_connection(
        self, connection: "AIOHttpClientConnectionUnified"
    ) -> None:
        """Validates an existing connection against the client config.

        Checks performed:
        * If ``force_http_2`` is enabled: Is the connection HTTP/2?
        """
        force_http_2 = self._config.force_http_2
        if force_http_2 and connection.version is not crt_http.HttpVersion.Http2:
            await connection.close()
            negotiated = crt_http.HttpVersion(connection.version).name
            raise SmithyHTTPError(f"HTTP/2 could not be negotiated: {negotiated}")

    def _render_path(self, url: core_interfaces.URI) -> str:
        path = url.path if url.path is not None else "/"
        query = f"?{url.query}" if url.query is not None else ""
        return f"{path}{query}"

    def _marshal_request(
        self, request: http_aio_interfaces.HTTPRequest
    ) -> "crt_http.HttpRequest":
        """Create :py:class:`awscrt.http.HttpRequest` from
        :py:class:`smithy_http.aio.HTTPRequest`"""
        headers_list: list[tuple[str, str]] = []
        if "host" not in request.fields:
            request.fields.set_field(
                Field(name="host", values=[request.destination.netloc])
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

        crt_request = crt_http.HttpRequest(
            method=request.method,
            path=path,
            headers=headers,
        )
        return crt_request

    async def _create_body_generator(
        self, body: core_aio_interfaces.StreamingBlob
    ) -> AsyncGenerator[bytes, None]:
        """Convert various body types to async generator for request_body_generator."""
        if isinstance(body, bytes):
            # Yield the entire body as a single chunk
            yield body
        elif isinstance(body, bytearray):
            # Convert bytearray to bytes
            yield bytes(body)
        elif isinstance(body, AsyncIterable):
            # Already async iterable, just yield from it.
            # Check this before AsyncByteStream since AsyncBytesReader implements both.
            async for chunk in body:
                if isinstance(chunk, bytearray):
                    yield bytes(chunk)
                else:
                    yield chunk
        elif iscoroutinefunction(getattr(body, "read", None)) and isinstance(
            body,  # type: ignore[reportGeneralTypeIssues]
            core_aio_interfaces.AsyncByteStream,  # type: ignore[reportGeneralTypeIssues]
        ):
            # AsyncByteStream has async read method but is not iterable
            while True:
                chunk = await body.read(self._config.read_buffer_size)
                if not chunk:
                    break
                if isinstance(chunk, bytearray):
                    yield bytes(chunk)
                else:
                    yield chunk
        else:
            # Assume it's a sync BytesReader, wrap it in AsyncBytesReader
            async_reader = AsyncBytesReader(body)
            async for chunk in async_reader:
                if isinstance(chunk, bytearray):
                    yield bytes(chunk)
                else:
                    yield chunk

    def __deepcopy__(self, memo: Any) -> "AWSCRTHTTPClient":
        return AWSCRTHTTPClient(
            eventloop=self._eventloop,
            client_config=deepcopy(self._config),
        )
