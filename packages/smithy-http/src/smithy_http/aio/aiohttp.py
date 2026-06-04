#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import weakref
from copy import deepcopy
from itertools import chain
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

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
from smithy_core.aio.utils import async_list
from smithy_core.exceptions import MissingDependencyError
from smithy_core.interfaces import URI

from .. import Field, Fields
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


class AIOHTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` using aiohttp."""

    TIMEOUT_EXCEPTIONS = (TimeoutError,)

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
        if _session is not None:
            self._session = _session
        else:
            # Disable transparent response decompression and advertise
            # 'identity' to request uncompressed responses.
            # TODO: add a functional test once the test client framework exists
            self._session = aiohttp.ClientSession(
                auto_decompress=False,
                headers={"Accept-Encoding": "identity"},
            )
            # Close the connector on GC/interpreter exit so aiohttp doesn't
            # emit "Unclosed client session"/"Unclosed connector" warnings
            # when the client is never closed explicitly.
            self._finalizer = weakref.finalize(self, self._close_session, self._session)

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
        request_config = request_config or HTTPRequestConfiguration()

        headers_list = list(
            chain.from_iterable(fld.as_tuples() for fld in request.fields)
        )

        body: StreamingBlob = request.body
        if not isinstance(body, AsyncBytesReader):
            body = AsyncBytesReader(body)

        # The typing on `params` is incorrect, it'll happily accept a mapping whose
        # values are lists (or tuples) and produce expected values.
        # See: https://github.com/aio-libs/aiohttp/issues/8563
        async with self._session.request(
            method=request.method,
            url=self._serialize_uri_without_query(request.destination),
            params=parse_qs(request.destination.query),  # type: ignore
            headers=headers_list,
            data=body,
        ) as resp:
            return await self._marshal_response(resp)

    def _serialize_uri_without_query(self, uri: URI) -> yarl.URL:
        """Serialize all parts of the URI up to and including the path."""
        return yarl.URL.build(
            scheme=uri.scheme or "",
            host=uri.host,
            port=uri.port,
            user=uri.username,
            password=uri.password,
            path=uri.path or "",
            encoded=True,
        )

    async def _marshal_response(
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
            body=async_list([await aiohttp_resp.read()]),
            reason=aiohttp_resp.reason,
        )

    def __deepcopy__(self, memo: Any) -> "AIOHTTPClient":
        return AIOHTTPClient(
            client_config=deepcopy(self._config),
            _session=self._session,
        )

    @staticmethod
    def _close_session(session: "aiohttp.ClientSession") -> None:
        """Synchronously close a session's connector.

        Runs from the :py:class:`weakref.finalize` hook, where there may be no
        running event loop, so we close the connector directly instead of
        awaiting ``session.close()``.
        """
        connector = session.connector
        if connector is not None and not connector.closed:
            connector._close()  # type: ignore[attr-defined]
