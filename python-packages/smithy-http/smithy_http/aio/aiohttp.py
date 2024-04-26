#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from copy import copy, deepcopy
from itertools import chain
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlunparse

if TYPE_CHECKING:
    # pyright doesn't like optional imports. This is reasonable because if we use these
    # in type hints then they'd result in runtime errors.
    # TODO: add integ tests that import these without the dependendency installed
    import aiohttp

try:
    import aiohttp  # noqa: F811

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False  # type: ignore

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import async_list
from smithy_core.exceptions import MissingDependencyException
from smithy_core.interfaces import URI

from .. import Field, Fields
from ..interfaces import (
    FieldPosition,
    HTTPClientConfiguration,
    HTTPRequestConfiguration,
)
from . import HTTPResponse
from .interfaces import HTTPClient, HTTPRequest
from .interfaces import HTTPResponse as HTTPResponseInterface


def _assert_aiohttp() -> None:
    if not HAS_AIOHTTP:
        raise MissingDependencyException(
            "Attempted to use aiohttp component, but aiohttp is not installed."
        )


class AIOHTTPClientConfig(HTTPClientConfiguration):
    def __post_init__(self) -> None:
        _assert_aiohttp()


class AIOHTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` using aiohttp."""

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
        self._session = _session or aiohttp.ClientSession()

    async def send(
        self,
        *,
        request: HTTPRequest,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponseInterface:
        """Send HTTP request using aiohttp client.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        request_config = request_config or HTTPRequestConfiguration()

        headers_list = list(
            chain.from_iterable(
                fld.as_tuples()
                for fld in request.fields.get_by_type(FieldPosition.HEADER)
            )
        )

        body: StreamingBlob = request.body
        if not isinstance(body, AsyncBytesReader):
            body = AsyncBytesReader(body)

        async with self._session.request(
            method=request.method,
            url=self._serialize_uri_without_query(request.destination),
            params=parse_qs(request.destination.query),
            headers=headers_list,
            data=body,
        ) as resp:
            return await self._marshal_response(resp)

    def _serialize_uri_without_query(self, uri: URI) -> str:
        """Serialize all parts of the URI up to and including the path."""
        components = (uri.scheme, uri.netloc, uri.path or "", "", "", "")
        return urlunparse(components)

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
                    kind=FieldPosition.HEADER,
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
            _session=copy(self._session),
        )
