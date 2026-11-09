#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Protocol

from smithy_core.aio.interfaces import AsyncClientTransport

from ...interfaces import (
    HTTPClientConfiguration,
    HTTPErrorIdentifier,
    HTTPRequest,
    HTTPRequestConfiguration,
    HTTPResponse,
)

__all__ = [
    "AsyncHTTPClient",
    "HTTPErrorIdentifier",
    "HTTPRequest",
    "HTTPResponse",
]


class AsyncHTTPClient(AsyncClientTransport[HTTPRequest, HTTPResponse], Protocol):
    """An asynchronous HTTP client interface.

    Header field names and values are not validated before reaching this
    layer. Implementations of ``AsyncHTTPClient`` are responsible for
    validating and handling those invalid and dangerous characters (such
    as CR, LF, or NUL) as defined in `RFC 9110, Section 5.5
    <https://www.rfc-editor.org/rfc/rfc9110#section-5.5>`_.
    """

    def __init__(self, *, client_config: HTTPClientConfiguration | None) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        ...

    async def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        """Send HTTP request over the wire and return the response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        ...
