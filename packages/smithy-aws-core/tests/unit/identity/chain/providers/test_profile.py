#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from smithy_aws_core.config.file_parser import Section
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_aws_core.identity.chain.providers.profile import (
    ProfileSessionCredentialsProvider,
    ProfileStaticCredentialsProvider,
)

from .conftest import OtherIdentity


@pytest.mark.parametrize(
    "provider",
    [ProfileSessionCredentialsProvider(), ProfileStaticCredentialsProvider()],
)
async def test_ignores_non_aws_identity_type(
    provider: Any,
    setup_provider: Callable[..., Awaitable[ChainSetup]],
) -> None:
    setup = await setup_provider(provider, identity_type=OtherIdentity)

    assert setup.resolvers == ()
    assert not setup.terminal


@pytest.mark.parametrize(
    "provider",
    [ProfileSessionCredentialsProvider(), ProfileStaticCredentialsProvider()],
)
async def test_requires_active_profile(
    provider: Any,
    setup_provider: Callable[..., Awaitable[ChainSetup]],
) -> None:
    setup = await setup_provider(provider)

    assert setup.resolvers == ()
    assert not setup.terminal


@pytest.mark.parametrize(
    "provider, profile, expected",
    [
        (
            ProfileSessionCredentialsProvider(),
            {
                "aws_access_key_id": "akid",
                "aws_secret_access_key": "secret",
                "aws_session_token": "token",
                "aws_account_id": "123456789012",
            },
            AWSCredentialsIdentity(
                access_key_id="akid",
                secret_access_key="secret",
                session_token="token",
                account_id="123456789012",
            ),
        ),
        (
            ProfileStaticCredentialsProvider(),
            {
                "aws_access_key_id": "akid",
                "aws_secret_access_key": "secret",
                "aws_account_id": "123456789012",
            },
            AWSCredentialsIdentity(
                access_key_id="akid",
                secret_access_key="secret",
                account_id="123456789012",
            ),
        ),
    ],
)
async def test_registers_terminal_resolver_for_complete_profile(
    provider: Any,
    profile: dict[str, str | dict[str, str]],
    expected: AWSCredentialsIdentity,
    setup_provider: Callable[..., Awaitable[ChainSetup]],
) -> None:
    setup = await setup_provider(provider, profile=Section(properties=profile))

    assert setup.terminal
    assert len(setup.resolvers) == 1
    identity = await setup.resolvers[0].get_identity(properties={})
    assert identity == expected


@pytest.mark.parametrize(
    "provider, properties",
    [
        (
            ProfileSessionCredentialsProvider(),
            {"aws_access_key_id": "akid", "aws_secret_access_key": "secret"},
        ),
        (ProfileStaticCredentialsProvider(), {"aws_access_key_id": "akid"}),
        (
            ProfileStaticCredentialsProvider(),
            {
                "aws_access_key_id": {"nested": "value"},
                "aws_secret_access_key": "secret",
            },
        ),
    ],
)
async def test_rejects_incomplete_or_non_string_keys(
    provider: Any,
    properties: dict[str, Any],
    setup_provider: Callable[..., Awaitable[ChainSetup]],
) -> None:
    setup = await setup_provider(provider, profile=Section(properties=properties))

    assert setup.resolvers == ()
    assert not setup.terminal
