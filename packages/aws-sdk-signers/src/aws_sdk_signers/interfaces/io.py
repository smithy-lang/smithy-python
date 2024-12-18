"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ByteStream(Protocol):
    """A file-like object with a read method that returns bytes."""

    def read(self, size: int = -1) -> bytes: ...


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes: ...
