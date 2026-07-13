# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from smithy_aws_core.config import load_config
from smithy_aws_core.config.merged_config import MergedConfig

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


class SharedConfigContext:
    """Resolution context shared across resolvers during config construction.

    Holds environment state and cached file data that resolvers use to
    look up values. Created once per resolve() call.
    """

    def __init__(
        self,
        *,
        profile_name: str | None = None,
        env: Mapping[str, str] | None = None,
        fs: FileSystem | None = None,
        http_client: Any | None = None,
        config_file_path: str | Path | None = None,
        credentials_file_path: str | Path | None = None,
    ) -> None:
        """Initialize the resolution context.

        :param profile_name: The active profile to use. Defaults to
            AWS_PROFILE env var, then "default".
        :param env: Environment variable mapping. Defaults to os.environ.
        :param fs: Filesystem abstraction for reading config files.
            Defaults to real disk I/O.
        :param http_client: HTTP client for network-based resolvers
            (e.g., IMDS).
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        """
        self._env: Mapping[str, str] = env if env is not None else os.environ
        self._fs: FileSystem = fs if fs is not None else DefaultFileSystem()
        self._http_client: Any | None = http_client
        self._profile_name: str = self._resolve_profile_name(profile_name)
        self._config_file_path: Path | None = (
            Path(config_file_path) if config_file_path is not None else None
        )
        self._credentials_file_path: Path | None = (
            Path(credentials_file_path) if credentials_file_path is not None else None
        )
        self._cached_config_file: MergedConfig | None = None

    @property
    def env(self) -> Mapping[str, str]:
        """The environment variable mapping."""
        return self._env

    @property
    def profile_name(self) -> str:
        """The active profile name."""
        return self._profile_name

    @property
    def fs(self) -> FileSystem:
        """The filesystem abstraction."""
        return self._fs

    @property
    def http_client(self) -> Any | None:
        """HTTP client for network-based resolvers."""
        return self._http_client

    async def parsed_profiles(self) -> MergedConfig:
        """Get the parsed and merged config/credentials file data.

        The result is cached after the first call so files are only
        read from disk once per context.
        """
        if self._cached_config_file is None:
            self._cached_config_file = await load_config(
                config_file_path=self._config_file_path,
                credentials_file_path=self._credentials_file_path,
            )
        return self._cached_config_file

    def _resolve_profile_name(self, explicit_profile: str | None) -> str:
        """Determine the active profile name.

        Priority: explicit argument > AWS_PROFILE env var > "default"
        """
        if explicit_profile is not None:
            return explicit_profile
        return self._env.get("AWS_PROFILE", "default")
