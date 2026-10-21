# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from ...config.exceptions import ConfigParseError
from ...config.file_parser import (
    RawParsedSections,
    _parse_content,  # type: ignore[reportPrivateUsage]
)
from .filesystem import FileSystem


async def parse_config_file(
    file_path: str, filesystem: FileSystem
) -> RawParsedSections:
    """Parse an AWS config or credentials file.

    Reads the file asynchronously and parses it into raw sections.

    :param file_path: Resolved path to the file.
    :param filesystem: FileSystem object to use.
    :returns: Raw sections dict {section_name: {key: value}}.
    :raises ConfigParseError: If the file has invalid syntax.
    """
    content = await filesystem.read_file(file_path)
    if content is None:
        return {}
    try:
        return _parse_content(content)
    except ConfigParseError as e:
        raise ConfigParseError(f"Unable to parse config file '{file_path}': {e}") from e
