# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field

from smithy_core import interfaces as core_interfaces
from smithy_core.aio import interfaces as core_aio_interfaces
from smithy_core.aio.utils import read_streaming_blob, read_streaming_blob_async

from .. import interfaces as http_interfaces
from . import interfaces as http_aio_interfaces


@dataclass(kw_only=True)
class HTTPRequest(http_aio_interfaces.HTTPRequest):
    """HTTP primitives for an Exchange to construct a version agnostic HTTP message."""

    destination: core_interfaces.URI
    body: core_aio_interfaces.StreamingBlob = field(repr=False, default=b"")
    method: str
    fields: http_interfaces.Fields


# HTTPResponse implements http_interfaces.HTTPResponse but cannot be explicitly
# annotated to reflect this because doing so causes Python to raise an AttributeError.
# See https://github.com/python/typing/discussions/903#discussioncomment-4866851 for
# details.
@dataclass(kw_only=True)
class HTTPResponse:
    """Basic implementation of :py:class:`.interfaces.HTTPResponse`.

    Implementations of :py:class:`.interfaces.HTTPClient` may return instances of this
    class or of custom response implementations.
    """

    body: core_aio_interfaces.StreamingBlob = field(repr=False, default=b"")
    """The response payload as iterable of chunks of bytes."""

    status: int
    """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""

    fields: http_interfaces.Fields
    """HTTP header and trailer fields."""

    reason: str | None = None
    """Optional string provided by the server explaining the status."""

    async def consume_body_async(self) -> bytes:
        """Iterate over response body and return as bytes."""
        return await read_streaming_blob_async(body=self.body)

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        return read_streaming_blob(body=self.body)
