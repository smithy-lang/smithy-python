# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path
from typing import Any

from .file_parser import (
    FileType,
    parse_config_file,
    standardize,
)
from .filesystem import DefaultFileSystem, FileSystem
from .merged_config import MergedConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_FILE = "~/.aws/config"
_DEFAULT_CREDENTIALS_FILE = "~/.aws/credentials"
_CONFIG_FILE_ENV_VAR = "AWS_CONFIG_FILE"
_CREDENTIALS_FILE_ENV_VAR = "AWS_SHARED_CREDENTIALS_FILE"
_PROFILE_ENV_VAR = "AWS_PROFILE"
_DEFAULT_PROFILE = "default"


def _resolve_config_paths(
    config_file_path: Path | None = None,
    credentials_file_path: Path | None = None,
) -> tuple[Path, Path]:
    """Resolve the final config and credentials file paths.

    Resolution order for each path:
    1. Explicit argument (if provided)
    2. Environment variable (AWS_CONFIG_FILE / AWS_SHARED_CREDENTIALS_FILE)
    3. Default (~/.aws/config / ~/.aws/credentials)

    The ~ is expanded to the user's home directory.

    :param config_file_path: Override path for config file.
    :param credentials_file_path: Override path for credentials file.
    :returns: Tuple of (resolved_config_path, resolved_credentials_path).
    """
    config_path = (
        config_file_path
        or Path(os.environ.get(_CONFIG_FILE_ENV_VAR, _DEFAULT_CONFIG_FILE))
    ).expanduser()

    credentials_path = (
        credentials_file_path
        or Path(os.environ.get(_CREDENTIALS_FILE_ENV_VAR, _DEFAULT_CREDENTIALS_FILE))
    ).expanduser()

    return config_path, credentials_path


async def load_config(
    config_file_path: Path | None = None,
    credentials_file_path: Path | None = None,
    fs: FileSystem | None = None,
) -> MergedConfig:
    """Load and merge AWS config and credentials files.

    Parses both files, standardizes them, and returns a merged
    MergedConfig ready for querying.

    :param config_file_path: Override path for config file.
        Defaults to AWS_CONFIG_FILE env var or ~/.aws/config.
    :param credentials_file_path: Override path for credentials file.
        Defaults to AWS_SHARED_CREDENTIALS_FILE env var or ~/.aws/credentials.
    :param fs: FileSystem to use for reading files.
        Defaults to DefaultFileSystem (real disk I/O).
    :returns: A MergedConfig with merged profiles from both files.
    """
    filesystem = fs or DefaultFileSystem()
    config_path, credentials_path = _resolve_config_paths(
        config_file_path, credentials_file_path
    )

    raw_config = await parse_config_file(str(config_path), filesystem)
    raw_credentials = await parse_config_file(str(credentials_path), filesystem)

    std_config = standardize(raw_config, FileType.CONFIG)
    std_credentials = standardize(raw_credentials, FileType.CREDENTIALS)

    return MergedConfig(std_config, std_credentials)


def shared_config_files_exist(
    config_file_path: Path | None = None,
    credentials_file_path: Path | None = None,
) -> bool:
    """Return whether either the shared config or credentials file exists.

    A cheap filesystem check (no parsing) used to detect whether the shared
    config credential source appears configured.

    :param config_file_path: Override path for config file.
        Defaults to AWS_CONFIG_FILE env var or ~/.aws/config.
    :param credentials_file_path: Override path for credentials file.
        Defaults to AWS_SHARED_CREDENTIALS_FILE env var or ~/.aws/credentials.
    :returns: True if either file exists on disk.
    """
    config_path, credentials_path = _resolve_config_paths(
        config_file_path, credentials_file_path
    )
    return config_path.is_file() or credentials_path.is_file()


class SharedConfigContext:
    """Resolution context shared across resolvers during config construction.

    Holds environment state and cached file data that resolvers use to
    look up values. Created once per resolve() call.
    """

    def __init__(
        self,
        *,
        profile_name: str | None = None,
        fs: FileSystem | None = None,
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
        self._fs: FileSystem = fs if fs is not None else DefaultFileSystem()
        self._http_client: Any | None = http_client
        self._profile_name, self._profile_origin = self._resolve_profile_name(
            profile_name
        )
        self._config_file_path: Path | None = (
            Path(config_file_path) if config_file_path is not None else None
        )
        self._credentials_file_path: Path | None = (
            Path(credentials_file_path) if credentials_file_path is not None else None
        )
        self._cached_config_file: MergedConfig | None = None

    @property
    def profile_name(self) -> str:
        """The active profile name."""
        return self._profile_name

    @property
    def profile_origin(self) -> str | None:
        """Where the active profile name came from, or None if it defaulted."""
        return self._profile_origin

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
                fs=self._fs,
            )
        return self._cached_config_file

    def _resolve_profile_name(
        self, explicit_profile: str | None
    ) -> tuple[str, str | None]:
        """Determine the active profile name and where it came from.

        Priority: explicit argument > AWS_PROFILE env var > "default"

        :returns: Tuple of (profile_name, origin), where origin describes the
            source for error messages and is None when the name was defaulted.
        """
        if explicit_profile is not None:
            return explicit_profile, "the profile argument"

        env_profile = os.environ.get(_PROFILE_ENV_VAR)
        if env_profile is not None:
            return env_profile, _PROFILE_ENV_VAR

        return _DEFAULT_PROFILE, None
