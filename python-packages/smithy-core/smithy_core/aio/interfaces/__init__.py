#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable

from ...interfaces import URI
from ...interfaces import StreamingBlob as SyncStreamingBlob


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes: ...


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
type StreamingBlob = SyncStreamingBlob | AsyncByteStream | AsyncIterable[bytes]


class Request(Protocol):
    """Protocol-agnostic representation of a request.

    :param destination: The URI where the request should be sent to.
    :param body: The request payload as iterable of chunks of bytes.
    """

    destination: URI
    body: StreamingBlob = b""

    async def consume_body_async(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...


class Response(Protocol):
    """Protocol-agnostic representation of a response."""

    @property
    def body(self) -> StreamingBlob:
        """The response payload as iterable of chunks of bytes."""
        ...

    async def consume_body_async(self) -> bytes:
        """Iterate over response body and return as bytes."""
        ...

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...
