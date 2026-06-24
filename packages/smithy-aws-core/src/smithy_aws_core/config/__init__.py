# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os

from smithy_aws_core.config.file_parser import (
    FileType,
    parse_config_file,
    standardize,
)
from smithy_aws_core.config.parsed_config_file import ParsedConfigFile

_DEFAULT_CONFIG_FILE = "~/.aws/config"
_DEFAULT_CREDENTIALS_FILE = "~/.aws/credentials"
_CONFIG_FILE_ENV_VAR = "AWS_CONFIG_FILE"
_CREDENTIALS_FILE_ENV_VAR = "AWS_SHARED_CREDENTIALS_FILE"


def resolve_config_paths(
    config_file_path: str | None = None,
    credentials_file_path: str | None = None,
) -> tuple[str, str]:
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
        config_file_path or os.environ.get(_CONFIG_FILE_ENV_VAR) or _DEFAULT_CONFIG_FILE
    )
    credentials_path = (
        credentials_file_path
        or os.environ.get(_CREDENTIALS_FILE_ENV_VAR)
        or _DEFAULT_CREDENTIALS_FILE
    )

    return (
        os.path.expanduser(os.path.expandvars(config_path)),
        os.path.expanduser(os.path.expandvars(credentials_path)),
    )


async def load_config(
    config_file_path: str | None = None,
    credentials_file_path: str | None = None,
) -> ParsedConfigFile:
    """Load and merge AWS config and credentials files.

    Parses both files, standardizes them, and returns a merged
    ParsedConfigFile ready for querying.

    :param config_file_path: Override path for config file.
        Defaults to AWS_CONFIG_FILE env var or ~/.aws/config.
    :param credentials_file_path: Override path for credentials file.
        Defaults to AWS_SHARED_CREDENTIALS_FILE env var or ~/.aws/credentials.
    :returns: A ParsedConfigFile with merged profiles from both files.
    """
    config_path, credentials_path = resolve_config_paths(
        config_file_path, credentials_file_path
    )

    raw_config = await parse_config_file(config_path)
    raw_credentials = await parse_config_file(credentials_path)

    std_config = standardize(raw_config, FileType.CONFIG)
    std_credentials = standardize(raw_credentials, FileType.CREDENTIALS)

    return ParsedConfigFile(std_config, std_credentials)
