# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol, runtime_checkable

__all__ = (
    "ByteStream",
    "ConditionallySeekable",
    "Seekable",
)


@runtime_checkable
class ByteStream(Protocol):
    """A file-like object with a read method that returns bytes."""

    def read(self, size: int | None = -1, /) -> bytes:
        """Read up to ``size`` bytes, or all remaining bytes if ``size`` is negative."""
        ...


@runtime_checkable
class Seekable(Protocol):
    """A file-like object with seek and tell implemented."""

    def seek(self, offset: int, whence: int = 0, /) -> int:
        """Move the stream position and return the new absolute position."""
        ...

    def tell(self) -> int:
        """Return the current stream position."""
        ...


@runtime_checkable
class ConditionallySeekable(Protocol):
    """A file-like object that is conditionally seekable.

    This is separate from Seekable as seekable objects may not define this method.
    """

    def seekable(self) -> bool:
        """Return whether the stream supports ``seek`` and ``tell``."""
        ...
