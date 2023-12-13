# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable
from dataclasses import dataclass

from smithy_core import interfaces as core_interfaces

from .. import interfaces as http_interfaces
from . import interfaces as http_aio_interfaces


@dataclass(kw_only=True)
class HTTPRequest(http_aio_interfaces.HTTPRequest):
    """HTTP primitives for an Exchange to construct a version agnostic HTTP message."""

    destination: core_interfaces.URI
    body: AsyncIterable[bytes]
    method: str
    fields: http_interfaces.Fields

    async def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        body = b""
        async for chunk in self.body:
            body += chunk
        return body


# HTTPResponse implements http_interfaces.http.HTTPResponse but cannot be explicitly
# annotated to reflect this because doing so causes Python to raise an AttributeError.
# See https://github.com/python/typing/discussions/903#discussioncomment-4866851 for
# details.
@dataclass(kw_only=True)
class HTTPResponse:
    """Basic implementation of :py:class:`...interfaces.http.HTTPResponse`.

    Implementations of :py:class:`...interfaces.http.HTTPClient` may return instances of
    this class or of custom response implementations.
    """

    body: AsyncIterable[bytes]
    """The response payload as iterable of chunks of bytes."""

    status: int
    """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""

    fields: http_interfaces.Fields
    """HTTP header and trailer fields."""

    reason: str | None = None
    """Optional string provided by the server explaining the status."""

    async def consume_body(self) -> bytes:
        """Iterate over response body and return as bytes."""
        body = b""
        async for chunk in self.body:
            body += chunk
        return body
