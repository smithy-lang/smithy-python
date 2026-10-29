# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
from typing import Protocol, runtime_checkable

from ...config.filesystem import DefaultFileSystem

__all__ = [
    "AsyncDefaultFileSystem",
    "AsyncFileSystem",
]

_SYNC_FILESYSTEM = DefaultFileSystem()


@runtime_checkable
class AsyncFileSystem(Protocol):
    """Protocol for filesystem operations.

    Abstraction over file I/O so tests can provide mock implementations
    without touching the real filesystem.
    """

    async def read_file(self, path: str) -> str | None:
        """Read a file's content as UTF-8.

        :param path: Resolved file path.
        :returns: File content, or None if the file is inaccessible.
        """
        ...


class AsyncDefaultFileSystem:
    """Default filesystem implementation using real disk I/O."""

    async def read_file(self, path: str) -> str | None:
        """Read a file asynchronously from disk.

        Missing files and permission errors return None with a warning.
        Encoding errors (invalid UTF-8) are raised to the caller.

        :param path: Resolved file path.
        :returns: File content, or None if the file is inaccessible.
        """
        return await asyncio.to_thread(_SYNC_FILESYSTEM.read_file, path)
