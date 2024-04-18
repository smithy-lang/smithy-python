#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable

from ...interfaces import StreamingBlob as SyncStreamingBlob


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes: ...


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
StreamingBlob = SyncStreamingBlob | AsyncByteStream | AsyncIterable[bytes]
