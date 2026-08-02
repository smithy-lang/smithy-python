#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
import asyncio
import json
import subprocess
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_aws_core.identity.chain.providers.process import (
    ProfileProcessCredentialsProvider,
    _split_process_command,
)
from smithy_aws_core.identity.process import ProcessCredentialsResolver

from .conftest import OtherIdentity


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("", []),
        ("spam eggs", ["spam", "eggs"]),
        ("spam\teggs", ["spam", "eggs"]),
        ("spam\neggs", ["spam\neggs"]),
        ('""', [""]),
        ('" "', [" "]),
        ('"\t"', ["\t"]),
        (r"spam \\", ["spam", r"\\"]),
        (r"\\", [r"\\"]),
        (r"\\ ", [r"\\"]),
        (r"\\	", [r"\\"]),
        (r"\"", ['"']),
        (
            r"C:\Tools\awscreds.exe --profile dev",
            [r"C:\Tools\awscreds.exe", "--profile", "dev"],
        ),
        (
            r'"C:\Program Files\awscreds.exe" --profile "test profile"',
            [r"C:\Program Files\awscreds.exe", "--profile", "test profile"],
        ),
        (r'"abc" d e', ["abc", "d", "e"]),
        (r'a\\b d"e f"g h', [r"a\\b", "de fg", "h"]),
        (r"a\\\"b c d", ['a\\"b', "c", "d"]),
        (r'a\\\\"b c" d e', [r"a\\b c", "d", "e"]),
    ],
)
def test_split_process_command_windows(
    command: str,
    expected: list[str],
) -> None:
    assert _split_process_command(command, platform="win32") == expected


@pytest.mark.parametrize(
    "arguments",
    [
        [r"C:\Tools\awscreds.exe", "--profile", "dev"],
        [r"C:\Program Files\awscreds.exe", "--profile", "test profile"],
        ["credential-helper", "", "embedded space"],
        ["credential-helper", 'embedded"quote', "trailing\\"],
        ["credential-helper", r"multiple\\backslashes", r'backslash\\"quote'],
    ],
)
def test_split_process_command_windows_round_trips_python_arguments(
    arguments: list[str],
) -> None:
    command = subprocess.list2cmdline(arguments)

    assert _split_process_command(command, platform="win32") == arguments


@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_split_process_command_posix(platform: str) -> None:
    command = r'/opt/My\ Tools/awscreds --profile "test profile"'

    assert _split_process_command(command, platform=platform) == [
        "/opt/My Tools/awscreds",
        "--profile",
        "test profile",
    ]


@pytest.mark.parametrize("platform", ["darwin", "linux", "win32"])
def test_split_process_command_rejects_unclosed_quote(platform: str) -> None:
    with pytest.raises(ValueError, match="No closing quotation"):
        _split_process_command('"credential-helper', platform=platform)


async def test_ignores_non_aws_identity_type(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
) -> None:
    provider = ProfileProcessCredentialsProvider()

    setup = await setup_provider(
        provider,
        identity_type=OtherIdentity,
        config_file=merged_config(
            {"default": {"credential_process": "credential-helper"}}
        ),
        profile_name="default",
    )

    assert setup.resolvers == ()
    assert not setup.terminal


async def test_requires_active_profile(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
) -> None:
    setup = await setup_provider(ProfileProcessCredentialsProvider())

    assert setup.resolvers == ()
    assert not setup.terminal


async def test_missing_process_does_not_register(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
) -> None:
    setup = await setup_provider(
        ProfileProcessCredentialsProvider(),
        config_file=merged_config({"default": {}}),
        profile_name="default",
    )

    assert setup.resolvers == ()
    assert not setup.terminal


async def test_registers_terminal_resolver(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
) -> None:
    setup = await setup_provider(
        ProfileProcessCredentialsProvider(),
        config_file=merged_config(
            {
                "default": {
                    "credential_process": (
                        'credential-helper --profile "test profile" --format json'
                    )
                }
            }
        ),
        profile_name="default",
    )

    assert setup.terminal
    assert len(setup.resolvers) == 1
    assert setup.resolvers[0].provider_name == "ProfileCredentialProcess"
    assert isinstance(setup.resolvers[0].resolver, ProcessCredentialsResolver)

    process = AsyncMock()
    process.returncode = 0
    process.communicate.return_value = (
        json.dumps(
            {
                "Version": 1,
                "AccessKeyId": "akid",
                "SecretAccessKey": "secret",
            }
        ).encode(),
        b"",
    )
    with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
        identity = await setup.resolvers[0].get_identity(properties={})

    assert identity.access_key_id == "akid"
    mock_exec.assert_called_once_with(
        "credential-helper",
        "--profile",
        "test profile",
        "--format",
        "json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
