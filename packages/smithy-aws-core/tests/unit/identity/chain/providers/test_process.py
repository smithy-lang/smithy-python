#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, patch

from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_aws_core.identity.chain.providers.process import (
    ProfileProcessCredentialsProvider,
)
from smithy_aws_core.identity.process import ProcessCredentialsResolver

from .conftest import OtherIdentity


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
