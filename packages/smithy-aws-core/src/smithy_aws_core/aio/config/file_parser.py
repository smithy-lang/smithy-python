# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from smithy_core.aio._program import run_program_async

from ...config.file_parser import (
    RawParsedSections,
    _parse_config_file,  # type: ignore[reportPrivateUsage]
)
from .filesystem import AsyncFileSystem


async def parse_config_file_async(
    file_path: str, filesystem: AsyncFileSystem
) -> RawParsedSections:
    """Parse an AWS config or credentials file.

    Reads the file asynchronously and parses it into raw sections.

    :param file_path: Resolved path to the file.
    :param filesystem: AsyncFileSystem object to use.
    :returns: Raw sections dict {section_name: {key: value}}.
    :raises ConfigParseError: If the file has invalid syntax.
    """
    return await run_program_async(_parse_config_file(file_path, filesystem))
