#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable, AsyncIterator
from copy import copy, deepcopy
from itertools import chain
from typing import TYPE_CHECKING, Any, Self

import yarl

if TYPE_CHECKING:
    # pyright doesn't like optional imports. This is reasonable because if we use these
    # in type hints then they'd result in runtime errors.
    # TODO: add integ tests that import these without the dependendency installed
    import aiohttp

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False  # type: ignore

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import MissingDependencyError
from smithy_core.interfaces import URI

from .. import Field, Fields
from ..exceptions import SmithyHTTPError
from ..interfaces import (
    HTTPClientConfiguration,
    HTTPRequestConfiguration,
)
from . import HTTPResponse
from .interfaces import HTTPClient, HTTPRequest
from .interfaces import HTTPResponse as HTTPResponseInterface


def _assert_aiohttp() -> None:
    if not HAS_AIOHTTP:
        raise MissingDependencyError(
            "Attempted to use aiohttp component, but aiohttp is not installed."
        )


class AIOHTTPClientConfig(HTTPClientConfiguration):
    def __post_init__(self) -> None:
        _assert_aiohttp()


class _AIOHTTPStreamingBody(AsyncIterable[bytes]):
    """Streams a response body, releasing the response once it is done."""

    def __init__(self, response: "aiohttp.ClientResponse") -> None:
        self._response = response

    def __aiter__(self) -> AsyncIterator[bytes]:
        # The reader iterates by line, so use iter_any to get raw chunks.
        return self._response.content.iter_any()

    async def close(self) -> None:
        # Pools the connection if the body was read to completion, closes it if not.
        self._response.release()


class AIOHTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` using aiohttp."""

    TIMEOUT_EXCEPTIONS = (TimeoutError,)

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

        headers_list = list(
            chain.from_iterable(fld.as_tuples() for fld in request.fields)
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
            data=body,
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

    async def __aenter__(self) -> Self:
        if self._closed:
            raise SmithyHTTPError("Cannot enter an HTTP client that has been closed.")
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()

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

    def _serialize_uri(self, uri: URI) -> yarl.URL:
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
        headers = Fields()
        for header_name, header_val in aiohttp_resp.headers.items():
            try:
                headers[header_name].add(header_val)
            except KeyError:
                headers[header_name] = Field(
                    name=header_name,
                    values=[header_val],
                    kind="header",
                )

        return HTTPResponse(
            status=aiohttp_resp.status,
            fields=headers,
            body=_AIOHTTPStreamingBody(aiohttp_resp),
            reason=aiohttp_resp.reason,
        )

    def __deepcopy__(self, memo: Any) -> "AIOHTTPClient":
        return AIOHTTPClient(
            client_config=deepcopy(self._config),
            _session=copy(self._session),
        )
