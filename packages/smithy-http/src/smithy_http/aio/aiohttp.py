#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable, AsyncIterator
from copy import copy, deepcopy
from itertools import chain
from typing import TYPE_CHECKING, Any, Self, cast

if TYPE_CHECKING:
    # pyright doesn't like optional imports. This is reasonable because if we use these
    # in type hints then they'd result in runtime errors.
    # TODO: add integ tests that import these without the dependendency installed
    import aiohttp
    import yarl

try:
    import aiohttp
    import yarl

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False  # type: ignore

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import MissingDependencyError
from smithy_core.interfaces import URI

from smithy_http import HTTPResponse
from smithy_http.interfaces import HTTPRequest
from smithy_http.interfaces import HTTPResponse as HTTPResponseInterface

from .. import tuples_to_fields
from ..exceptions import SmithyHTTPError
from ..interfaces import (
    HTTPClientConfiguration,
    HTTPRequestConfiguration,
)
from .interfaces import AsyncHTTPClient

__all__ = ["HAS_AIOHTTP", "AIOHTTPClient", "AIOHTTPClientConfig"]

_UPLOAD_CHUNK_SIZE = 128 * 1024


class AIOHTTPClientConfig(HTTPClientConfiguration):
    """Configuration for the aiohttp HTTP client."""

    def __post_init__(self) -> None:
        _assert_aiohttp()


class AIOHTTPClient(AsyncHTTPClient):
    """Implementation of :py:class:`.interfaces.AsyncHTTPClient` using aiohttp."""

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = (TimeoutError,)

    # aiohttp has no HTTP/2 support, so it can never interleave request and
    # response data.
    SUPPORTS_DUPLEX_STREAMING = False

    def __init__(
        self,
        *,
        client_config: AIOHTTPClientConfig | None = None,
        _session: "aiohttp.ClientSession | None" = None,
    ) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        _assert_aiohttp()
        self._config = client_config or AIOHTTPClientConfig()
        self._closed = False
        # Disable transparent response decompression and advertise
        # 'identity' to request uncompressed responses.
        # TODO: add a functional test once the test client framework exists
        self._session = _session or aiohttp.ClientSession(
            auto_decompress=False,
            headers={"Accept-Encoding": "identity"},
        )

    async def __aenter__(self) -> Self:
        if self._closed:
            raise SmithyHTTPError("Cannot enter an HTTP client that has been closed.")
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()

    def __deepcopy__(self, memo: Any) -> "AIOHTTPClient":
        return AIOHTTPClient(
            client_config=deepcopy(self._config),
            _session=copy(self._session),
        )

    async def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponseInterface:
        """Send HTTP request using aiohttp client.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        if self._closed:
            raise SmithyHTTPError(
                "Cannot send a request after the HTTP client has been closed."
            )

        request_config = request_config or HTTPRequestConfiguration()

        # aiohttp chunks a body itself when asked with chunked=True, and rejects a
        # Transfer-Encoding: chunked header, so the header becomes that flag.
        chunked = "transfer-encoding" in request.fields and [
            value.strip().lower()
            for value in request.fields["transfer-encoding"].values
        ] == ["chunked"]
        # aiohttp can't send request trailers, and a trailer is never a header.
        headers_list = list(
            chain.from_iterable(
                fld.as_tuples()
                for fld in request.fields.get_by_type("header")
                if not (chunked and fld.name.lower() == "transfer-encoding")
            )
        )

        body: StreamingBlob | None = request.body
        if (
            "content-length" not in request.fields
            and "transfer-encoding" not in request.fields
        ):
            body = await self._prepare_body(body)
        elif not isinstance(body, AsyncBytesReader):
            body = AsyncBytesReader(body)

        resp = await self._session.request(
            method=request.method,
            url=self._serialize_uri(request.destination),
            headers=headers_list,
            data=_upload_data(request.body, body),
            chunked=True if chunked else None,
            allow_redirects=False,
            skip_auto_headers={"Content-Type"},
        )
        try:
            return self._marshal_response(resp)
        except BaseException:
            resp.release()
            raise

    async def close(self) -> None:
        """Close the underlying aiohttp session and its connection pool."""
        if self._closed:
            return
        self._closed = True
        await self._session.close()

    async def _prepare_body(self, body: StreamingBlob) -> AsyncBytesReader | None:
        """Convert a body for aiohttp, omitting seekable bodies with no data."""
        if not isinstance(body, AsyncBytesReader):
            body = AsyncBytesReader(body)

        if not body.seekable():
            return body

        position = await body.seek(0, 1)
        end = await body.seek(0, 2)
        await body.seek(position)
        return None if position == end else body

    def _serialize_uri(self, uri: URI) -> "yarl.URL":
        """Serialize the URI, preserving the already-encoded query string as-is."""
        return yarl.URL.build(
            scheme=uri.scheme or "",
            host=uri.host,
            port=uri.port,
            user=uri.username,
            password=uri.password,
            path=uri.path or "",
            query_string=uri.query or "",
            encoded=True,
        )

    def _marshal_response(
        self, aiohttp_resp: "aiohttp.ClientResponse"
    ) -> HTTPResponseInterface:
        """Convert a ``aiohttp.ClientResponse`` to a ``smithy_http.aio.HTTPResponse``"""
        return HTTPResponse(
            status=aiohttp_resp.status,
            fields=tuples_to_fields(aiohttp_resp.headers.items()),
            body=_AIOHTTPStreamingBody(aiohttp_resp),
            reason=aiohttp_resp.reason,
        )


def _upload_data(source: Any, body: AsyncBytesReader | None) -> Any:
    """What aiohttp uploads for a request body, which it iterates.

    A reader is read in 128 KiB chunks, which uploads faster than the 64 KiB that
    AsyncBytesReader iterates in by default. An async iterable that isn't a reader
    is passed through, so each item is sent as soon as it's produced rather than
    held until a chunk fills.
    """
    if body is None:
        return None
    if not hasattr(source, "read") and isinstance(source, AsyncIterable):
        return cast(AsyncIterable[bytes], source)
    return body.iter_chunks(_UPLOAD_CHUNK_SIZE)


def _assert_aiohttp() -> None:
    if not HAS_AIOHTTP:
        raise MissingDependencyError(
            "Attempted to use aiohttp component, but aiohttp is not installed."
        )


class _AIOHTTPStreamingBody(AsyncIterable[bytes]):
    """Streams a response body, releasing the response once it is done."""

    def __init__(self, response: "aiohttp.ClientResponse") -> None:
        self._response = response
        self._reader: AsyncBytesReader | None = None

    def __aiter__(self) -> AsyncIterator[bytes]:
        # The reader iterates by line, so use iter_any to get raw chunks.
        return self._response.content.iter_any()

    async def read(self, size: int = -1) -> bytes:
        if self._reader is None:
            self._reader = AsyncBytesReader(self._response.content.iter_any())
        return await self._reader.read(size)

    async def close(self) -> None:
        # Pools the connection if the body was read to completion, closes it if not.
        self._response.release()
