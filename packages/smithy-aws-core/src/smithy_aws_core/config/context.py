# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from pathlib import Path
from typing import Any

from smithy_core._program import Program, run_program

from .file_parser import (
    FileType,
    _parse_config_file,  # pyright: ignore[reportPrivateUsage]
    standardize,
)
from .filesystem import DefaultFileSystem, FileSystem
from .merged_config import MergedConfig
from .types import ConfigSource

__all__ = ["SharedConfigContext", "load_config", "shared_config_files_exist"]

logger = logging.getLogger(__name__)

_PROFILE_ENV_VAR = "AWS_PROFILE"
_DEFAULT_PROFILE = "default"

_DEFAULT_CONFIG_FILE = "~/.aws/config"
_DEFAULT_CREDENTIALS_FILE = "~/.aws/credentials"
_CONFIG_FILE_ENV_VAR = "AWS_CONFIG_FILE"
_CREDENTIALS_FILE_ENV_VAR = "AWS_SHARED_CREDENTIALS_FILE"


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


def _load_config(
    config_file_path: Path | None, credentials_file_path: Path | None, fs: Any
) -> Program[MergedConfig]:
    config_path, credentials_path = _resolve_config_paths(
        config_file_path, credentials_file_path
    )

    raw_config = yield from _parse_config_file(str(config_path), fs)
    raw_credentials = yield from _parse_config_file(str(credentials_path), fs)

    std_config = standardize(raw_config, FileType.CONFIG)
    std_credentials = standardize(raw_credentials, FileType.CREDENTIALS)

    return MergedConfig(std_config, std_credentials)


def load_config(
    config_file_path: Path | None = None,
    credentials_file_path: Path | None = None,
    fs: FileSystem | None = None,
) -> MergedConfig:
    """Load and merge AWS config and credentials files.

    :param config_file_path: Override path for config file.
        Defaults to AWS_CONFIG_FILE env var or ~/.aws/config.
    :param credentials_file_path: Override path for credentials file.
        Defaults to AWS_SHARED_CREDENTIALS_FILE env var or ~/.aws/credentials.
    :param fs: FileSystem to use for reading files. Defaults to real disk I/O.
    :returns: A MergedConfig with merged profiles from both files.
    """
    return run_program(
        _load_config(config_file_path, credentials_file_path, fs or DefaultFileSystem())
    )


class _SharedConfigContextBase:
    """Resolution context logic shared by the sync and async contexts."""

    def __init__(
        self,
        *,
        profile_name: str | None,
        fs: Any,
        http_client: Any | None,
        config_file_path: str | Path | None,
        credentials_file_path: str | Path | None,
    ) -> None:
        self._fs = fs
        self._http_client: Any | None = http_client
        self._profile_name, self._profile_source = self._resolve_profile_name(
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
    def profile_source(self) -> ConfigSource:
        """The source of the active profile name."""
        return self._profile_source

    @property
    def http_client(self) -> Any | None:
        """HTTP client for network-based resolvers."""
        return self._http_client

    def __deepcopy__(self, memo: Any) -> Any:
        """Return self rather than a copy.

        The context is read-only once resolution finishes: resolvers have
        already pulled their values onto the config's fields, and nothing on
        the request path reads it again. Generated clients deep-copy the
        config on every operation call to keep plugin mutations scoped to
        that call, which would otherwise rebuild the whole parsed profile
        tree per request — work proportional to the size of the caller's
        shared config files. Sharing this instead keeps that cost flat
        without weakening the isolation of the fields plugins actually write.
        """
        return self

    def _parsed_profiles(self) -> Program[MergedConfig]:
        if self._cached_config_file is None:
            self._cached_config_file = yield from _load_config(
                self._config_file_path, self._credentials_file_path, self._fs
            )
        return self._cached_config_file

    def _resolve_profile_name(
        self, explicit_profile: str | None
    ) -> tuple[str, ConfigSource]:
        """Determine the active profile name and where it came from.

        Priority: explicit argument > AWS_PROFILE env var > "default"

        :returns: Tuple of (profile_name, source), where source is the
            provenance of the name: ``OVERRIDE`` for the explicit argument,
            ``ENV`` for ``AWS_PROFILE``, and ``DEFAULT`` for the fallback.
        """
        if explicit_profile is not None:
            return explicit_profile, ConfigSource.OVERRIDE

        env_profile = os.environ.get(_PROFILE_ENV_VAR)
        if env_profile:
            return env_profile, ConfigSource.ENV

        return _DEFAULT_PROFILE, ConfigSource.DEFAULT


class SharedConfigContext(_SharedConfigContextBase):
    """Resolution context shared across resolvers during config construction.

    Holds environment state and cached file data that resolvers use to look up
    values. Created once per resolve() call.
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
        :param http_client: HTTP client for network-based resolvers.
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        """
        super().__init__(
            profile_name=profile_name,
            fs=fs if fs is not None else DefaultFileSystem(),
            http_client=http_client,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )

    @property
    def fs(self) -> FileSystem:
        """The filesystem abstraction."""
        return self._fs

    def parsed_profiles(self) -> MergedConfig:
        """Get the parsed and merged config/credentials file data.

        The result is cached after the first call so files are only read from
        disk once per context.
        """
        return run_program(self._parsed_profiles())
