# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from typing import Any

from smithy_core.aio._program import run_program_async

from ...config.context import (
    _load_config,  # type: ignore[reportPrivateUsage]
    _SharedConfigContextBase,  # type: ignore[reportPrivateUsage]
)
from ...config.merged_config import MergedConfig
from .filesystem import AsyncDefaultFileSystem, AsyncFileSystem


async def load_config_async(
    config_file_path: Path | None = None,
    credentials_file_path: Path | None = None,
    fs: AsyncFileSystem | None = None,
) -> MergedConfig:
    """Load and merge AWS config and credentials files.

    Parses both files, standardizes them, and returns a merged
    MergedConfig ready for querying.

    :param config_file_path: Override path for config file.
        Defaults to AWS_CONFIG_FILE env var or ~/.aws/config.
    :param credentials_file_path: Override path for credentials file.
        Defaults to AWS_SHARED_CREDENTIALS_FILE env var or ~/.aws/credentials.
    :param fs: AsyncFileSystem to use for reading files.
        Defaults to AsyncDefaultFileSystem (real disk I/O).
    :returns: A MergedConfig with merged profiles from both files.
    """
    return await run_program_async(
        _load_config(
            config_file_path, credentials_file_path, fs or AsyncDefaultFileSystem()
        )
    )


class AsyncSharedConfigContext(_SharedConfigContextBase):
    """Resolution context shared across resolvers during config construction.

    Holds environment state and cached file data that resolvers use to
    look up values. Created once per resolve() call.
    """

    def __init__(
        self,
        *,
        profile_name: str | None = None,
        fs: AsyncFileSystem | None = None,
        http_client: Any | None = None,
        config_file_path: str | Path | None = None,
        credentials_file_path: str | Path | None = None,
    ) -> None:
        """Initialize the resolution context.

        :param profile_name: The active profile to use. Defaults to
            AWS_PROFILE env var, then "default".
        :param fs: Filesystem abstraction for reading config files.
            Defaults to real disk I/O.
        :param http_client: HTTP client for network-based resolvers
            (e.g., IMDS).
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        """
        super().__init__(
            profile_name=profile_name,
            fs=fs if fs is not None else AsyncDefaultFileSystem(),
            http_client=http_client,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )

    @property
    def fs(self) -> AsyncFileSystem:
        """The filesystem abstraction."""
        return self._fs

    async def parsed_profiles(self) -> MergedConfig:
        """Get the parsed and merged config/credentials file data.

        The result is cached after the first call so files are only
        read from disk once per context.
        """
        return await run_program_async(self._parsed_profiles())
