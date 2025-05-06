#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol

from smithy_core.aio.interfaces import ClientTransport, Request, Response
from smithy_core.aio.utils import read_streaming_blob, read_streaming_blob_async
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID

from ...interfaces import (
    Fields,
    HTTPClientConfiguration,
    HTTPRequestConfiguration,
)


class HTTPRequest(Request, Protocol):
    """HTTP primitive for an Exchange to construct a version agnostic HTTP message.

    :param destination: The URI where the request should be sent to.
    :param method: The HTTP method of the request, for example "GET".
    :param fields: ``Fields`` object containing HTTP headers and trailers.
    :param body: A streamable collection of bytes.
    """

    method: str
    fields: Fields

    async def consume_body_async(self) -> bytes:
        """Iterate over request body and return as bytes."""
        return await read_streaming_blob_async(self.body)

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        return read_streaming_blob(self.body)


class HTTPResponse(Response, Protocol):
    """HTTP primitives returned from an Exchange, used to construct a client
    response."""

    @property
    def status(self) -> int:
        """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""
        ...

    @property
    def fields(self) -> Fields:
        """``Fields`` object containing HTTP headers and trailers."""
        ...

    @property
    def reason(self) -> str | None:
        """Optional string provided by the server explaining the status."""
        ...

    async def consume_body_async(self) -> bytes:
        """Iterate over request body and return as bytes."""
        return await read_streaming_blob_async(self.body)

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        return read_streaming_blob(self.body)


class HTTPClient(ClientTransport[HTTPRequest, HTTPResponse], Protocol):
    """An asynchronous HTTP client interface."""

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


class HTTPErrorIdentifier:
    """A class that uses HTTP response metadata to identify errors.

    The body of the response SHOULD NOT be touched by this. The payload codec will be
    used instead to check for an ID in the body.
    """

    def identify(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
    ) -> ShapeID | None:
        """Idenitfy the ShapeID of an error from an HTTP response."""
