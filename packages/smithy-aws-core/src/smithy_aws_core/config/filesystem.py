# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class FileSystem(Protocol):
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


class DefaultFileSystem:
    """Default filesystem implementation using real disk I/O."""

    async def read_file(self, path: str) -> str | None:
        """Read a file asynchronously from disk.

        Missing files and permission errors return None with a warning.
        Encoding errors (invalid UTF-8) are raised to the caller.

        :param path: Resolved file path.
        :returns: File content, or None if the file is inaccessible.
        """
        try:
            content: str = await asyncio.to_thread(
                Path(path).read_text, encoding="utf-8"
            )
            return content
        except FileNotFoundError:
            return None
        except (PermissionError, OSError) as e:
            logger.warning("Unable to read config file '%s': %s", path, e)
            return None
