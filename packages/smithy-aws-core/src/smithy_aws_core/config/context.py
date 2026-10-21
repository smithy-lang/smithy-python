# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path

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
