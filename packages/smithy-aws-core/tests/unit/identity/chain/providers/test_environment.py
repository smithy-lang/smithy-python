#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable, Mapping

import pytest
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_aws_core.identity.chain.providers.environment import (
    EnvironmentCredentialsProvider,
)
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

from .conftest import OtherIdentity


async def test_ignores_non_aws_identity_type(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(
        EnvironmentCredentialsProvider(), identity_type=OtherIdentity
    )

    assert setup.resolvers == ()
    assert not setup.terminal


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {"AWS_ACCESS_KEY_ID": "akid"},
        {"AWS_SECRET_ACCESS_KEY": "secret"},
    ],
)
async def test_requires_both_keys(
    environment: dict[str, str],
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    setup = await setup_provider(EnvironmentCredentialsProvider())

    assert setup.resolvers == ()
    assert not setup.terminal


async def test_registers_terminal_resolver(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(EnvironmentCredentialsProvider())

    assert setup.terminal
    assert len(setup.resolvers) == 1
    assert setup.resolvers[0].provider_name == "Environment"
    assert isinstance(setup.resolvers[0].resolver, EnvironmentCredentialsResolver)


async def test_skips_when_profile_uses_environment_credential_source(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    config = merged_config(
        {
            "assume": {
                "role_arn": "arn:aws:iam::123456789012:role/example",
                "credential_source": "Environment",
            }
        }
    )

    setup = await setup_provider(
        EnvironmentCredentialsProvider(),
        config_file=config,
        profile_name="assume",
    )

    assert setup.resolvers == ()
    assert not setup.terminal


@pytest.mark.parametrize(
    "profile_properties",
    [
        {
            "role_arn": "arn:aws:iam::123456789012:role/example",
            "credential_source": "Ec2InstanceMetadata",
        },
        {"credential_source": "Environment"},
        {"role_arn": "arn:aws:iam::123456789012:role/example"},
    ],
)
async def test_registers_resolver_when_not_assuming_role_from_environment(
    profile_properties: Mapping[str, str],
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    config = merged_config({"assume": profile_properties})

    setup = await setup_provider(
        EnvironmentCredentialsProvider(),
        config_file=config,
        profile_name="assume",
    )

    assert setup.terminal
    assert len(setup.resolvers) == 1
    assert isinstance(setup.resolvers[0].resolver, EnvironmentCredentialsResolver)


async def test_registers_resolver_when_profile_missing_from_config(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(
        EnvironmentCredentialsProvider(),
        config_file=merged_config({}),
        profile_name="does-not-exist",
    )

    assert setup.terminal
    assert len(setup.resolvers) == 1
    assert isinstance(setup.resolvers[0].resolver, EnvironmentCredentialsResolver)
